"""Fal: Tencent Hunyuan3D 3.1 image-to-3D."""

from ..base import GenerateRequest, ParamSpec
from ..common import data_uri
from .queue import FalQueueProvider


class FalHunyuan3DProvider(FalQueueProvider):
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
            "input_image_url": data_uri(req.image),
            "face_count": p.get("face_count", 50000),
            "generate_type": p.get("generate_type", "Normal"),
            "enable_pbr": p.get("enable_pbr", False),
        }
