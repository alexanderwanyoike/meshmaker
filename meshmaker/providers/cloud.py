"""Hosted image-to-3D providers.

Each provider calls a cloud REST API with the user's own API key and returns an
``Asset`` pointing at a hosted GLB URL. HTTP transport lives in ``meshmaker.api``;
the provider classes only build requests and map responses.

To add a Generate provider: subclass ``Provider`` here, implement ``generate``,
and register the instance in ``registry.py``.
"""

import base64
import time

from .. import api
from .base import Asset, GenerateRequest, Provider

_POLL_INTERVAL = 5
_POLL_TIMEOUT = 600


class ProviderError(Exception):
    """Raised when a hosted provider fails to return a usable model."""


def _data_uri(image: bytes, mime: str = "image/png") -> str:
    """Encode raw image bytes as a base64 data URI (accepted by Fal and Meshy)."""
    encoded = base64.b64encode(image).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


# --- Fal: Hunyuan3D 3.1 Pro -------------------------------------------------


class FalHunyuan3DProvider(Provider):
    """Tencent Hunyuan3D 3.1 Pro image-to-3D, hosted on Fal's queue API."""

    id = "FAL_HUNYUAN3D"
    name = "Hunyuan3D 3.1 (Fal)"
    description = "Tencent Hunyuan3D 3.1 Pro image-to-3D, hosted on Fal"
    api_key_pref_field = "fal_api_key"

    # Swap to "fal-ai/hunyuan-3d/v3.1/rapid/image-to-3d" for the cheaper/faster tier.
    model_id = "fal-ai/hunyuan-3d/v3.1/pro/image-to-3d"

    def generate(self, req: GenerateRequest) -> Asset:
        headers = {"Authorization": f"Key {req.api_key}"}
        payload = {
            "input_image_url": _data_uri(req.image),
            "face_count": req.face_count,
            "enable_pbr": req.enable_pbr,
        }

        submit = api.http_post_json(
            f"https://queue.fal.run/{self.model_id}", payload, headers,
        )
        status_url = submit.get("status_url")
        response_url = submit.get("response_url")
        if not status_url or not response_url:
            raise ProviderError(f"Fal submit returned no queue URLs: {submit}")

        result = self._poll(status_url, response_url, headers)

        url = (result.get("model_glb") or {}).get("url")
        if not url:
            url = ((result.get("model_urls") or {}).get("glb") or {}).get("url")
        if not url:
            raise ProviderError(f"Fal response had no GLB URL: {result}")

        return Asset(
            url=url,
            format="glb",
            metadata={"provider": self.id, "seed": result.get("seed")},
        )

    def _poll(self, status_url, response_url, headers):
        deadline = time.monotonic() + _POLL_TIMEOUT
        while time.monotonic() < deadline:
            status = api.http_get_json(status_url, headers, timeout=90)
            state = status.get("status")
            if state == "COMPLETED":
                return api.http_get_json(response_url, headers, timeout=_POLL_TIMEOUT)
            if state in ("IN_QUEUE", "IN_PROGRESS"):
                time.sleep(_POLL_INTERVAL)
                continue
            raise ProviderError(f"Fal job in unexpected state: {status}")
        raise ProviderError(f"Fal job timed out after {_POLL_TIMEOUT}s")


# --- Meshy: Image to 3D -----------------------------------------------------


class MeshyProvider(Provider):
    """Meshy image-to-3D (textured), via the Meshy OpenAPI."""

    id = "MESHY"
    name = "Meshy"
    description = "Meshy image-to-3D, textured"
    api_key_pref_field = "meshy_api_key"

    base_url = "https://api.meshy.ai"
    # "latest" tracks Meshy's newest model (meshy-6); pin to "meshy-5" for stability.
    ai_model = "latest"

    def generate(self, req: GenerateRequest) -> Asset:
        headers = {"Authorization": f"Bearer {req.api_key}"}
        payload = {
            "image_url": _data_uri(req.image),
            "ai_model": self.ai_model,
            "should_texture": True,
            "enable_pbr": req.enable_pbr,
            "target_polycount": req.face_count,
            "target_formats": ["glb"],
        }

        created = api.http_post_json(
            f"{self.base_url}/openapi/v1/image-to-3d", payload, headers,
        )
        task_id = created.get("result") or created.get("id")
        if not task_id:
            raise ProviderError(f"Meshy create returned no task id: {created}")

        task = self._poll(f"{self.base_url}/openapi/v1/image-to-3d/{task_id}", headers)

        url = (task.get("model_urls") or {}).get("glb")
        if not url:
            raise ProviderError(f"Meshy task had no GLB URL: {task}")

        return Asset(
            url=url,
            format="glb",
            metadata={
                "provider": self.id,
                "task_id": task_id,
                "consumed_credits": task.get("consumed_credits"),
            },
        )

    def _poll(self, task_url, headers):
        deadline = time.monotonic() + _POLL_TIMEOUT
        while time.monotonic() < deadline:
            task = api.http_get_json(task_url, headers, timeout=90)
            state = task.get("status")
            if state == "SUCCEEDED":
                return task
            if state in ("FAILED", "CANCELED"):
                message = (task.get("task_error") or {}).get("message", "")
                raise ProviderError(f"Meshy task {state}: {message}")
            time.sleep(_POLL_INTERVAL)
        raise ProviderError(f"Meshy task timed out after {_POLL_TIMEOUT}s")
