"""Shared building blocks for hosted providers: errors, image encoding, poll policy.

Kept dependency-free (no ``bpy``) so the provider modules and their tests import
without Blender.
"""

import base64

_POLL_INTERVAL = 5
# Generous: heavy models (e.g. Fal pro) can spend many minutes in cold-start and
# queue before compute begins. Timing out too early would discard a job the
# provider is still running - and that the user has already paid for.
_POLL_TIMEOUT = 1800


class ProviderError(Exception):
    """Raised when a hosted provider fails to return a usable model."""


def data_uri(image: bytes, mime: str = "image/png") -> str:
    """Encode raw image bytes as a base64 data URI (accepted by Fal and Meshy)."""
    encoded = base64.b64encode(image).decode("utf-8")
    return f"data:{mime};base64,{encoded}"
