"""HTTP transport for MeshMaker (stdlib only).

Two concerns live here: generic JSON/asset HTTP helpers used by the hosted
providers (Fal, Meshy), and the Gemini client used to generate concept images.
No third-party dependencies so the addon installs as a plain Blender zip.
"""

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


class HttpError(Exception):
    pass


def _request_json(req, timeout):
    try:
        with _urlopen_with_retry(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise HttpError(f"HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise HttpError(f"Connection error: {e.reason}") from e


def http_post_json(url, payload, headers=None, timeout=120):
    """POST a JSON body and return the parsed JSON response."""
    merged = {"Content-Type": "application/json"}
    if headers:
        merged.update(headers)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=merged, method="POST")
    return _request_json(req, timeout)


def http_get_json(url, headers=None, timeout=120):
    """GET a URL and return the parsed JSON response."""
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    return _request_json(req, timeout)


def download(url, timeout=600):
    """Download a URL and return its raw bytes (for hosted GLB assets)."""
    req = urllib.request.Request(url, method="GET")
    try:
        with _urlopen_with_retry(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise HttpError(f"HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise HttpError(f"Connection error: {e.reason}") from e


class GeminiError(Exception):
    pass


def call_gemini(api_key, model, prompt, image_b64=None, timeout=120):
    """Call Gemini to generate or edit an image.

    Args:
        api_key: Gemini API key.
        model: Model name (e.g. "gemini-2.5-flash-image").
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
