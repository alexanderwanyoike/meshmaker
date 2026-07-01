"""Fal: TencentARC Pixal3D pixel-aligned image-to-3D."""

from ..base import GenerateRequest, ParamSpec
from ..common import data_uri
from .queue import FalQueueProvider


class FalPixal3DProvider(FalQueueProvider):
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
            "image_url": data_uri(req.image),
            "resolution": int(p.get("resolution", 1024)),
            "texture_size": int(p.get("texture_size", 2048)),
            "remesh": p.get("remesh", True),
            "decimation_target": p.get("decimation_target", 200000),
        }
