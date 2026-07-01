"""Fal: Hyper3D Rodin image-to-3D."""

from ..base import GenerateRequest, ParamSpec
from ..common import data_uri
from .queue import FalQueueProvider


class FalRodinProvider(FalQueueProvider):
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
            "input_image_urls": [data_uri(req.image)],
            "geometry_file_format": "glb",
            "quality": p.get("quality", "medium"),
            "material": p.get("material", "PBR"),
            "tier": p.get("tier", "Regular"),
            "hyper_mode": p.get("hyper_mode", False),
        }
