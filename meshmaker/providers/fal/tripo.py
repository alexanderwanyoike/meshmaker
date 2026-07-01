"""Fal: Tripo v2.5 image-to-3D."""

from ..base import GenerateRequest, ParamSpec
from ..common import data_uri
from .queue import FalQueueProvider


class FalTripoProvider(FalQueueProvider):
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
            "image_url": data_uri(req.image),
            "texture": p.get("texture", "standard"),
            "pbr": p.get("pbr", True),
            "quad": p.get("quad", False),
            "face_limit": p.get("face_limit", 50000),
        }
