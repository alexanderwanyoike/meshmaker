"""Tests for meshmaker/api.py - HTTP helpers and the Gemini client."""

import base64
import importlib.util
import io
import json
import os
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

# Import api.py directly to avoid meshmaker/__init__.py pulling in bpy
_api_path = os.path.join(os.path.dirname(__file__), "..", "meshmaker", "api.py")
_spec = importlib.util.spec_from_file_location("meshmaker_api", _api_path)
api = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(api)


def _make_http_response(body_dict):
    """Create a mock HTTP response with JSON body."""
    data = json.dumps(body_dict).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = data
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _patch_api(name):
    """Patch a name on the api module directly (avoids bpy import)."""
    return patch.object(api, name) if hasattr(api, name) else patch(f"meshmaker_api.{name}")


def _patch_urlopen():
    return patch.object(api.urllib.request, "urlopen")


def _patch_retry():
    return patch.object(api, "_urlopen_with_retry")


def _patch_sleep():
    return patch.object(api.time, "sleep")


class TestUrlOpenWithRetry(unittest.TestCase):
    def test_success_first_try(self):
        with _patch_urlopen() as mock_urlopen:
            resp = _make_http_response({"ok": True})
            mock_urlopen.return_value = resp
            result = api._urlopen_with_retry("http://example.com", timeout=10)
            self.assertEqual(result, resp)
            self.assertEqual(mock_urlopen.call_count, 1)

    def test_retries_on_dns_failure(self):
        with _patch_urlopen() as mock_urlopen, _patch_sleep() as mock_sleep:
            dns_error = urllib.error.URLError("Name or service not known")
            resp = _make_http_response({"ok": True})
            mock_urlopen.side_effect = [dns_error, resp]
            result = api._urlopen_with_retry("http://example.com", timeout=10)
            self.assertEqual(result, resp)
            self.assertEqual(mock_urlopen.call_count, 2)
            mock_sleep.assert_called_once_with(api._DNS_RETRY_DELAY)

    def test_retries_on_temp_resolution_failure(self):
        with _patch_urlopen() as mock_urlopen, _patch_sleep():
            dns_error = urllib.error.URLError("Temporary failure in name resolution")
            resp = _make_http_response({"ok": True})
            mock_urlopen.side_effect = [dns_error, dns_error, resp]
            result = api._urlopen_with_retry("http://example.com", timeout=10)
            self.assertEqual(result, resp)
            self.assertEqual(mock_urlopen.call_count, 3)

    def test_raises_after_max_retries(self):
        with _patch_urlopen() as mock_urlopen, _patch_sleep():
            dns_error = urllib.error.URLError("Name or service not known")
            mock_urlopen.side_effect = [dns_error] * 3
            with self.assertRaises(urllib.error.URLError):
                api._urlopen_with_retry("http://example.com", timeout=10)
            self.assertEqual(mock_urlopen.call_count, 3)

    def test_non_dns_error_not_retried(self):
        with _patch_urlopen() as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
            with self.assertRaises(urllib.error.URLError):
                api._urlopen_with_retry("http://example.com", timeout=10)
            self.assertEqual(mock_urlopen.call_count, 1)


class TestCallGemini(unittest.TestCase):
    def _gemini_response(self, image_b64="aW1n", text="done", has_image=True):
        parts = []
        if has_image:
            parts.append({
                "inlineData": {"mimeType": "image/png", "data": image_b64},
            })
        if text:
            parts.append({"text": text})
        return {"candidates": [{"content": {"parts": parts}}]}

    def test_text_to_image(self):
        with _patch_retry() as mock_fetch:
            img_bytes = b"\x89PNG_fake_image"
            img_b64 = base64.b64encode(img_bytes).decode()
            mock_fetch.return_value = _make_http_response(
                self._gemini_response(image_b64=img_b64, text="here you go")
            )
            result_bytes, result_text = api.call_gemini("key", "model", "a robot")
            self.assertEqual(result_bytes, img_bytes)
            self.assertEqual(result_text, "here you go")

            # Verify request payload
            req = mock_fetch.call_args[0][0]
            payload = json.loads(req.data.decode("utf-8"))
            self.assertEqual(len(payload["contents"][0]["parts"]), 1)
            self.assertEqual(payload["contents"][0]["parts"][0]["text"], "a robot")
            self.assertEqual(
                payload["generationConfig"]["responseModalities"], ["IMAGE", "TEXT"]
            )

    def test_edit_mode_sends_image(self):
        with _patch_retry() as mock_fetch:
            img_b64 = base64.b64encode(b"result").decode()
            mock_fetch.return_value = _make_http_response(
                self._gemini_response(image_b64=img_b64)
            )
            existing_b64 = base64.b64encode(b"existing").decode()
            api.call_gemini("key", "model", "make it blue", image_b64=existing_b64)

            req = mock_fetch.call_args[0][0]
            payload = json.loads(req.data.decode("utf-8"))
            parts = payload["contents"][0]["parts"]
            # Image part comes before text part
            self.assertEqual(len(parts), 2)
            self.assertIn("inlineData", parts[0])
            self.assertEqual(parts[0]["inlineData"]["data"], existing_b64)
            self.assertEqual(parts[1]["text"], "make it blue")

    def test_no_image_in_response_raises(self):
        with _patch_retry() as mock_fetch:
            mock_fetch.return_value = _make_http_response(
                self._gemini_response(has_image=False, text="sorry no image")
            )
            with self.assertRaises(api.GeminiError) as ctx:
                api.call_gemini("key", "model", "a cat")
            self.assertIn("No image", str(ctx.exception))

    def test_no_candidates_raises(self):
        with _patch_retry() as mock_fetch:
            mock_fetch.return_value = _make_http_response({"candidates": []})
            with self.assertRaises(api.GeminiError) as ctx:
                api.call_gemini("key", "model", "a cat")
            self.assertIn("No candidates", str(ctx.exception))

    def test_api_error_raises(self):
        with _patch_retry() as mock_fetch:
            mock_fetch.return_value = _make_http_response(
                {"error": {"message": "quota exceeded"}}
            )
            with self.assertRaises(api.GeminiError) as ctx:
                api.call_gemini("key", "model", "a cat")
            self.assertIn("quota exceeded", str(ctx.exception))

    def test_http_error_raises(self):
        with _patch_retry() as mock_fetch:
            mock_fetch.side_effect = urllib.error.HTTPError(
                "url", 403, "Forbidden", {}, io.BytesIO(b"bad key")
            )
            with self.assertRaises(api.GeminiError) as ctx:
                api.call_gemini("key", "model", "a cat")
            self.assertIn("HTTP 403", str(ctx.exception))

    def test_url_contains_model_and_key(self):
        with _patch_retry() as mock_fetch:
            img_b64 = base64.b64encode(b"img").decode()
            mock_fetch.return_value = _make_http_response(
                self._gemini_response(image_b64=img_b64)
            )
            api.call_gemini("mykey", "gemini-2.5-flash-image", "test")
            req = mock_fetch.call_args[0][0]
            self.assertIn("gemini-2.5-flash-image", req.full_url)
            self.assertIn("key=mykey", req.full_url)


class TestHttpHelpers(unittest.TestCase):
    def test_post_json_sends_payload_and_headers(self):
        with _patch_retry() as mock_fetch:
            mock_fetch.return_value = _make_http_response({"status_url": "s"})
            result = api.http_post_json(
                "https://queue.fal.run/model",
                {"input_image_url": "data:..."},
                {"Authorization": "Key abc"},
            )
            self.assertEqual(result, {"status_url": "s"})

            req = mock_fetch.call_args[0][0]
            self.assertEqual(req.full_url, "https://queue.fal.run/model")
            self.assertEqual(req.get_method(), "POST")
            payload = json.loads(req.data.decode("utf-8"))
            self.assertEqual(payload["input_image_url"], "data:...")
            # Header keys are normalized to capitalized form by urllib
            self.assertEqual(req.headers["Authorization"], "Key abc")
            self.assertEqual(req.headers["Content-type"], "application/json")

    def test_get_json_sends_headers(self):
        with _patch_retry() as mock_fetch:
            mock_fetch.return_value = _make_http_response({"status": "COMPLETED"})
            result = api.http_get_json("https://q/status", {"Authorization": "Key abc"})
            self.assertEqual(result, {"status": "COMPLETED"})

            req = mock_fetch.call_args[0][0]
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(req.headers["Authorization"], "Key abc")

    def test_http_error_raises_httperror(self):
        with _patch_retry() as mock_fetch:
            mock_fetch.side_effect = urllib.error.HTTPError(
                "url", 401, "Unauthorized", {}, io.BytesIO(b"bad key")
            )
            with self.assertRaises(api.HttpError) as ctx:
                api.http_get_json("https://q/status")
            self.assertIn("HTTP 401", str(ctx.exception))

    def test_download_returns_bytes(self):
        with _patch_retry() as mock_fetch:
            resp = MagicMock()
            resp.read.return_value = b"glb-bytes"
            resp.__enter__ = MagicMock(return_value=resp)
            resp.__exit__ = MagicMock(return_value=False)
            mock_fetch.return_value = resp

            data = api.download("https://fal.media/model.glb")
            self.assertEqual(data, b"glb-bytes")

            req = mock_fetch.call_args[0][0]
            self.assertEqual(req.full_url, "https://fal.media/model.glb")
            self.assertEqual(req.get_method(), "GET")

    def test_download_http_error_raises(self):
        with _patch_retry() as mock_fetch:
            mock_fetch.side_effect = urllib.error.HTTPError(
                "url", 404, "Not Found", {}, io.BytesIO(b"gone")
            )
            with self.assertRaises(api.HttpError) as ctx:
                api.download("https://fal.media/missing.glb")
            self.assertIn("HTTP 404", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
