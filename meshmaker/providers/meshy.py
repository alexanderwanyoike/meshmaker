"""Meshy image-to-3D provider (textured), via the Meshy OpenAPI."""

import time

from .. import api
from .base import Asset, GenerateRequest, ParamSpec, Provider
from .common import _POLL_INTERVAL, _POLL_TIMEOUT, ProviderError, data_uri


class MeshyProvider(Provider):
    """Meshy image-to-3D (textured), via the Meshy OpenAPI."""

    id = "MESHY"
    name = "Meshy"
    description = "Meshy image-to-3D, textured"
    api_key_pref_field = "meshy_api_key"

    base_url = "https://api.meshy.ai"

    params = (
        ParamSpec(
            "ai_model", "Model", "enum", "latest",
            items=(("meshy-5", "Meshy 5"), ("meshy-6", "Meshy 6"), ("latest", "Latest")),
        ),
        # Without remesh, Meshy ignores target_polycount and returns the native
        # (very high poly) mesh. On by default so Face Count actually applies.
        ParamSpec(
            "should_remesh", "Remesh", "bool", True,
            description="Remesh to the target polycount (off returns the raw, very dense mesh)",
        ),
        ParamSpec(
            "target_polycount", "Target Polycount", "int", 50000, min=25000, max=300000,
            description="Only applies when Remesh is on",
        ),
        ParamSpec(
            "topology", "Topology", "enum", "triangle",
            items=(("triangle", "Triangle"), ("quad", "Quad")),
            description="Only applies when Remesh is on",
        ),
        ParamSpec("should_texture", "Texture", "bool", True),
        ParamSpec(
            "enable_pbr", "PBR Materials", "bool", False,
            description="Only applies when Texture is on",
        ),
    )

    def generate(self, req: GenerateRequest) -> Asset:
        p = req.params
        headers = {"Authorization": f"Bearer {req.api_key}"}
        payload = {
            "image_url": data_uri(req.image),
            "ai_model": p.get("ai_model", "latest"),
            "should_remesh": p.get("should_remesh", True),
            "target_polycount": p.get("target_polycount", 50000),
            "topology": p.get("topology", "triangle"),
            "should_texture": p.get("should_texture", True),
            "enable_pbr": p.get("enable_pbr", False),
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
