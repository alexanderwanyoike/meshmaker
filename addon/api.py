"""API clients for RunPod (Trellis 2) and Gemini (image generation)."""

import base64
import json
import time
import urllib.error
import urllib.request

_DNS_RETRIES = 3
_DNS_RETRY_DELAY = 2


def _urlopen_with_retry(req, timeout):
    """urlopen wrapper that retries on transient DNS/connection errors."""
    for attempt in range(_DNS_RETRIES):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.URLError as e:
            is_dns = "Name or service not known" in str(e.reason)
            is_conn = "Temporary failure in name resolution" in str(e.reason)
            if (is_dns or is_conn) and attempt < _DNS_RETRIES - 1:
                time.sleep(_DNS_RETRY_DELAY)
                continue
            raise
    raise urllib.error.URLError("DNS resolution failed after retries")


class RunPodError(Exception):
    pass


def call_runpod(api_key, endpoint_id, payload, timeout=600):
    """Call a RunPod serverless endpoint and return the result.

    Submits via /run (async) then polls /status until completion.
    Uses only stdlib (urllib) so there are no external dependencies.

    Args:
        api_key: RunPod API key.
        endpoint_id: RunPod endpoint ID.
        payload: Dict with the "input" key for the endpoint.
        timeout: Max seconds to wait for the job to complete.

    Returns:
        The output dict from the RunPod response.

    Raises:
        RunPodError: On API errors, timeouts, or missing output.
    """
    url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with _urlopen_with_retry(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RunPodError(f"HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RunPodError(f"Connection error: {e.reason}") from e

    if "error" in result:
        raise RunPodError(result["error"])

    job_id = result.get("id")
    if not job_id:
        raise RunPodError("No job ID in response")

    # Poll for completion. The COMPLETED response includes the full output
    # (20MB+ base64 GLB), so we use a generous read timeout and catch ALL
    # exceptions — any transient failure (DNS, socket timeout, incomplete
    # read, connection reset) just triggers a retry on the next iteration.
    status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        time.sleep(5)

        try:
            status_req = urllib.request.Request(status_url, headers=headers)
            with _urlopen_with_retry(status_req, timeout=90) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except Exception:
            # Any failure during polling (DNS, socket, read, parse) —
            # retry on next iteration instead of crashing
            continue

        status = result.get("status")
        if status == "COMPLETED":
            output = result.get("output")
            if output is None:
                raise RunPodError("Job completed but output is empty")
            return output
        elif status == "FAILED":
            raise RunPodError(f"Job failed: {json.dumps(result, default=str)}")

    raise RunPodError(f"Job {job_id} timed out after {timeout}s")


class GeminiError(Exception):
    pass


def call_gemini(api_key, model, prompt, image_b64=None, timeout=120):
    """Call Gemini to generate or edit an image.

    Args:
        api_key: Gemini API key.
        model: Model name (e.g. "gemini-2.5-flash-preview-image-generation").
        prompt: Text prompt for generation or editing.
        image_b64: Optional base64-encoded image for editing mode.
        timeout: Request timeout in seconds.

    Returns:
        (image_bytes, text_response) tuple. text_response may be empty.

    Raises:
        GeminiError: On API errors or missing image in response.
    """
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model}:generateContent?key={api_key}"
    )

    parts = []
    if image_b64 is not None:
        parts.append({
            "inlineData": {"mimeType": "image/png", "data": image_b64},
        })
    parts.append({"text": prompt})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with _urlopen_with_retry(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise GeminiError(f"HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise GeminiError(f"Connection error: {e.reason}") from e

    if "error" in result:
        msg = result["error"].get("message", json.dumps(result["error"]))
        raise GeminiError(msg)

    candidates = result.get("candidates", [])
    if not candidates:
        raise GeminiError("No candidates in response")

    response_parts = candidates[0].get("content", {}).get("parts", [])

    image_bytes = None
    text_response = ""

    for part in response_parts:
        inline = part.get("inlineData")
        if inline and inline.get("mimeType", "").startswith("image/"):
            image_bytes = base64.b64decode(inline["data"])
        if "text" in part:
            text_response = part["text"]

    if image_bytes is None:
        raise GeminiError("No image in response")

    return image_bytes, text_response
