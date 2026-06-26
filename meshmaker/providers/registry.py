"""Provider registry and lookup helpers."""

from .base import Capability, Provider
from .runpod import HUNYUAN3D, HYMOTION, MIA, P3SAM, TRELLIS2


_PROVIDERS: tuple[Provider, ...] = (
    TRELLIS2,
    HUNYUAN3D,
    MIA,
    HYMOTION,
    P3SAM,
)


def list_providers() -> tuple[Provider, ...]:
    return _PROVIDERS


def providers_for(capability: Capability) -> tuple[Provider, ...]:
    return tuple(provider for provider in _PROVIDERS if provider.supports(capability))


def resolve(capability: Capability, provider_id: str | None = None) -> Provider:
    candidates = providers_for(capability)
    if not candidates:
        raise LookupError(f"No provider registered for {capability.value}")

    if provider_id is None:
        return candidates[0]

    for provider in candidates:
        if provider.id == provider_id:
            return provider

    raise LookupError(f"No provider '{provider_id}' for {capability.value}")
