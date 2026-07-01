"""Fal-hosted image-to-3D providers.

Each model is one module here; all share the queue transport in ``queue.py`` and
the ``fal_api_key`` preference. Add a Fal model by dropping a new module beside
these and re-exporting its provider class below, then register the instance in
``providers/registry.py``.
"""

from .hunyuan3d import FalHunyuan3DProvider
from .pixal3d import FalPixal3DProvider
from .rodin import FalRodinProvider
from .tripo import FalTripoProvider

__all__ = [
    "FalHunyuan3DProvider",
    "FalPixal3DProvider",
    "FalRodinProvider",
    "FalTripoProvider",
]
