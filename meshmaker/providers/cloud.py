"""Hosted image-to-3D providers.

Each provider calls a cloud REST API with the user's own API key and returns an
``Asset`` pointing at a hosted GLB URL. HTTP transport lives in ``meshmaker.api``;
the provider classes only build requests and map responses.

To add a Generate provider: subclass ``Provider`` here, implement ``generate``,
and register the instance in ``registry.py``. Fal-hosted models can subclass
``_FalQueueProvider`` instead and only declare ``endpoint``/``params``/``_payload``
- the queue submit/poll mechanics are shared.
"""

import base64
import time

from .. import api
from .base import Asset, GenerateRequest, ParamSpec, Provider

_POLL_INTERVAL = 5
# Generous: heavy models (e.g. Fal pro) can spend many minutes in cold-start and
# queue before compute begins. Timing out too early would discard a job the
# provider is still running - and that the user has already paid for.
_POLL_TIMEOUT = 1800


class ProviderError(Exception):
    """Raised when a hosted provider fails to return a usable model."""


def _data_uri(image: bytes, mime: str = "image/png") -> str:
    """Encode raw image bytes as a base64 data URI (accepted by Fal and Meshy)."""
    encoded = base64.b64encode(image).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def _fal_glb_url(result: dict) -> str | None:
    """Pull the GLB download url from a Fal result across known output shapes.

    Different Fal 3D models nest the url differently: ``model_urls.glb.url``
    (Hunyuan3D), ``model_glb.url`` (Hunyuan3D, Pixal3D), or ``model_mesh.url``
    (Tripo, Rodin). ``model_urls.glb`` wins because ``model_glb`` is polymorphic -
    on some Hunyuan tiers it points at an OBJ, whereas ``model_urls.glb`` is
    always GLB.
    """
    url = ((result.get("model_urls") or {}).get("glb") or {}).get("url")
    if url:
        return url
    url = (result.get("model_glb") or {}).get("url")
    if url:
        return url
    return (result.get("model_mesh") or {}).get("url")


# --- Fal queue transport ----------------------------------------------------


class _FalQueueProvider(Provider):
    """Shared transport for Fal queue-API image-to-3D providers.

    Every Fal provider submits one job to ``https://queue.fal.run/{endpoint}`` with
    ``Key`` auth, polls the returned ``status_url`` until ``COMPLETED``, then reads
    the GLB url from the result. Subclasses declare ``endpoint`` and ``params`` and
    implement ``_payload``; the queue mechanics live here once. All Fal providers
    share the same ``fal_api_key`` preference.
    """

    api_key_pref_field = "fal_api_key"
    endpoint: str = ""

    def _endpoint(self, params: dict) -> str:
        """The Fal model id to submit to (may depend on params, e.g. a tier)."""
        return self.endpoint

    def _payload(self, req: GenerateRequest) -> dict:
        raise NotImplementedError

    def generate(self, req: GenerateRequest) -> Asset:
        headers = {"Authorization": f"Key {req.api_key}"}

        submit = api.http_post_json(
            f"https://queue.fal.run/{self._endpoint(req.params)}",
            self._payload(req),
            headers,
        )
        status_url = submit.get("status_url")
        response_url = submit.get("response_url")
        if not status_url or not response_url:
            raise ProviderError(f"Fal submit returned no queue URLs: {submit}")

        result = self._poll(status_url, response_url, headers)

        url = _fal_glb_url(result)
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


# --- Fal: Hunyuan3D 3.1 -----------------------------------------------------


class FalHunyuan3DProvider(_FalQueueProvider):
    """Tencent Hunyuan3D 3.1 image-to-3D, hosted on Fal's queue API."""

    id = "FAL_HUNYUAN3D"
    name = "Hunyuan3D 3.1 (Fal)"
    description = "Tencent Hunyuan3D 3.1 image-to-3D, hosted on Fal"

    params = (
        ParamSpec(
            "tier", "Tier", "enum", "pro",
            items=(("pro", "Pro (quality)"), ("rapid", "Rapid (fast/cheap)")),
            description="Pro is higher quality and slower; Rapid is faster and cheaper",
        ),
        # Fal's API hard-floors face_count at 40,000 - it cannot honestly go lower.
        ParamSpec(
            "face_count", "Face Count", "int", 50000, min=40000, max=1500000,
            description="Target polygon count (Fal minimum is 40,000)",
        ),
        ParamSpec(
            "generate_type", "Type", "enum", "Normal",
            items=(("Normal", "Normal"), ("Geometry", "Geometry (no texture)")),
            description="Geometry returns an untextured white model",
        ),
        ParamSpec("enable_pbr", "PBR Materials", "bool", False),
    )

    def _endpoint(self, params: dict) -> str:
        tier = params.get("tier", "pro")
        return f"fal-ai/hunyuan-3d/v3.1/{tier}/image-to-3d"

    def _payload(self, req: GenerateRequest) -> dict:
        p = req.params
        return {
            "input_image_url": _data_uri(req.image),
            "face_count": p.get("face_count", 50000),
            "generate_type": p.get("generate_type", "Normal"),
            "enable_pbr": p.get("enable_pbr", False),
        }


# --- Fal: Pixal3D -----------------------------------------------------------


class FalPixal3DProvider(_FalQueueProvider):
    """TencentARC Pixal3D pixel-aligned image-to-3D, hosted on Fal."""

    id = "FAL_PIXAL3D"
    name = "Pixal3D (Fal)"
    description = "TencentARC Pixal3D pixel-aligned image-to-3D, hosted on Fal"
    endpoint = "fal-ai/pixal3d"

    params = (
        ParamSpec(
            "resolution", "Resolution", "enum", "1024",
            items=(("1024", "1024p"), ("1536", "1536p")),
            description="Higher resolution is slower but more detailed",
        ),
        ParamSpec(
            "texture_size", "Texture Size", "enum", "2048",
            items=(("1024", "1024"), ("2048", "2048"), ("4096", "4096")),
        ),
        ParamSpec(
            "remesh", "Remesh", "bool", True,
            description="Decimate to the target (off returns the raw, dense mesh)",
        ),
        ParamSpec(
            "decimation_target", "Decimation Target", "int", 200000,
            min=5000, max=1500000,
            description="Target face count when Remesh is on",
        ),
    )

    def _payload(self, req: GenerateRequest) -> dict:
        p = req.params
        return {
            "image_url": _data_uri(req.image),
            "resolution": int(p.get("resolution", 1024)),
            "texture_size": int(p.get("texture_size", 2048)),
            "remesh": p.get("remesh", True),
            "decimation_target": p.get("decimation_target", 200000),
        }


# --- Fal: Tripo v2.5 --------------------------------------------------------


class FalTripoProvider(_FalQueueProvider):
    """Tripo v2.5 image-to-3D, hosted on Fal."""

    id = "FAL_TRIPO"
    name = "Tripo (Fal)"
    description = "Tripo v2.5 image-to-3D, hosted on Fal"
    endpoint = "tripo3d/tripo/v2.5/image-to-3d"

    params = (
        ParamSpec(
            "texture", "Texture", "enum", "standard",
            items=(("no", "None"), ("standard", "Standard"), ("HD", "HD")),
        ),
        ParamSpec("pbr", "PBR Materials", "bool", True),
        ParamSpec(
            "quad", "Quad Topology", "bool", False,
            description="Remesh to quad faces instead of triangles",
        ),
        ParamSpec(
            "face_limit", "Face Limit", "int", 50000, min=1000, max=500000,
            description="Target face count",
        ),
    )

    def _payload(self, req: GenerateRequest) -> dict:
        p = req.params
        return {
            "image_url": _data_uri(req.image),
            "texture": p.get("texture", "standard"),
            "pbr": p.get("pbr", True),
            "quad": p.get("quad", False),
            "face_limit": p.get("face_limit", 50000),
        }


# --- Fal: Hyper3D Rodin -----------------------------------------------------


class FalRodinProvider(_FalQueueProvider):
    """Hyper3D Rodin image-to-3D, hosted on Fal."""

    id = "FAL_RODIN"
    name = "Rodin (Fal)"
    description = "Hyper3D Rodin image-to-3D, hosted on Fal"
    endpoint = "fal-ai/hyper3d/rodin"

    params = (
        ParamSpec(
            "quality", "Quality", "enum", "medium",
            items=(
                ("high", "High"), ("medium", "Medium"),
                ("low", "Low"), ("extra-low", "Extra Low"),
            ),
            description="Higher quality is slower and denser",
        ),
        ParamSpec(
            "material", "Material", "enum", "PBR",
            items=(("PBR", "PBR"), ("Shaded", "Shaded")),
        ),
        ParamSpec(
            "tier", "Tier", "enum", "Regular",
            items=(("Regular", "Regular"), ("Sketch", "Sketch (fast/cheap)")),
        ),
        ParamSpec(
            "hyper_mode", "Hyper Mode", "bool", False,
            description="Enhanced quality (slower, costs more)",
        ),
    )

    def _payload(self, req: GenerateRequest) -> dict:
        p = req.params
        # Rodin takes an array of image urls (multi-view); a single reference is
        # the common case here.
        return {
            "input_image_urls": [_data_uri(req.image)],
            "geometry_file_format": "glb",
            "quality": p.get("quality", "medium"),
            "material": p.get("material", "PBR"),
            "tier": p.get("tier", "Regular"),
            "hyper_mode": p.get("hyper_mode", False),
        }


# --- Meshy: Image to 3D -----------------------------------------------------


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
            "image_url": _data_uri(req.image),
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
