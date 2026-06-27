"""Registry of MeshMaker Generate providers.

To add a provider: implement a ``Provider`` subclass in ``cloud.py`` and add its
instance to ``_PROVIDERS`` below. The Blender UI builds its model dropdown from
this list, so nothing else needs to change.
"""

from .base import Provider
from .cloud import FalHunyuan3DProvider, MeshyProvider

FAL_HUNYUAN3D = FalHunyuan3DProvider()
MESHY = MeshyProvider()

_PROVIDERS: tuple[Provider, ...] = (
    FAL_HUNYUAN3D,
    MESHY,
)


def list_providers() -> tuple[Provider, ...]:
    return _PROVIDERS


def resolve(provider_id: str | None = None) -> Provider:
    if not _PROVIDERS:
        raise LookupError("No Generate providers registered")
    if provider_id is None:
        return _PROVIDERS[0]
    for provider in _PROVIDERS:
        if provider.id == provider_id:
            return provider
    raise LookupError(f"No provider '{provider_id}'")
