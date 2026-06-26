"""Provider contracts for MeshMaker Generate backends.

MeshMaker is image-to-3D only. The Blender UI builds a typed ``GenerateRequest``
and consumes an ``Asset``. Each hosted backend (Fal, Meshy, ...) is one
``Provider`` subclass in ``cloud.py``. Adding a new Generate provider is a single
class there plus one line in ``registry.py`` - nothing else changes.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Asset:
    """A generated 3D model, returned by a provider as a hosted download URL.

    Providers never return inline bytes; the client downloads ``url`` and imports
    it. ``format`` is the file extension (``glb`` today).
    """

    url: str
    format: str = "glb"
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerateRequest:
    """A provider-agnostic image-to-3D request.

    ``image`` is the raw reference image bytes (PNG/JPEG). Providers encode it as a
    base64 data URI; both Fal and Meshy accept inline data URIs, so there is no
    separate image-upload step.
    """

    api_key: str
    image: bytes
    face_count: int = 50000
    enable_pbr: bool = False


class Provider:
    """Base class for a Generate (image-to-3D) provider."""

    id: str
    name: str
    description: str = ""
    # Name of the addon preference holding this provider's API key.
    api_key_pref_field: str = ""

    def generate(self, req: GenerateRequest) -> Asset:
        raise NotImplementedError
