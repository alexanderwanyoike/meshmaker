"""Provider contracts for MeshMaker Generate backends.

MeshMaker is image-to-3D only. The Blender UI builds a typed ``GenerateRequest``
and consumes an ``Asset``. Each hosted backend (Fal, Meshy, ...) is one
``Provider`` subclass in ``cloud.py``. Adding a new Generate provider is a single
class there plus one line in ``registry.py`` - nothing else changes.

Each provider declares its own ``params`` (a tuple of ``ParamSpec``) - the real
controls of its API. The Blender UI renders these dynamically, so switching
provider switches the visible knobs, and the provider maps them to its request.
Nothing is faked or post-processed: the addon imports exactly what the provider
returns.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ParamSpec:
    """One provider control, rendered as a Blender property in the panel."""

    key: str
    label: str
    kind: str  # "int" | "bool" | "enum"
    default: Any
    min: int | None = None
    max: int | None = None
    items: tuple[tuple[str, str], ...] = ()  # (value, label) pairs for "enum"
    description: str = ""


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

    ``image`` is the raw reference image bytes (PNG/JPEG). ``params`` carries the
    values for the selected provider's ``ParamSpec`` controls; each provider reads
    the keys it declared.
    """

    api_key: str
    image: bytes
    params: dict[str, Any] = field(default_factory=dict)


class Provider:
    """Base class for a Generate (image-to-3D) provider."""

    id: str
    name: str
    description: str = ""
    # Name of the addon preference holding this provider's API key.
    api_key_pref_field: str = ""
    # The provider's real, UI-exposed controls.
    params: tuple[ParamSpec, ...] = ()

    def generate(self, req: GenerateRequest) -> Asset:
        raise NotImplementedError
