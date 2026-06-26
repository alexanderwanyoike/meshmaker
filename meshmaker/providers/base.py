"""Base provider contracts.

The Blender UI should build typed requests and consume Asset objects. Transport
details such as legacy base64 RunPod responses stay inside provider classes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Capability(Enum):
    GENERATE = "generate"
    SEGMENT = "segment"
    RIG = "rig"
    MOTION = "motion"
    VIDEO_MOTION = "video_motion"


@dataclass(frozen=True)
class Asset:
    """A generated file.

    `data` is a temporary compatibility path for existing base64 handlers.
    Card 02 replaces it with URL-backed assets.
    """

    format: str
    metadata: dict[str, Any] = field(default_factory=dict)
    url: str | None = None
    data: bytes | None = None
    name: str | None = None

    def require_data(self) -> bytes:
        if self.data is None:
            raise ValueError("Asset has no inline data; URL download is not implemented yet")
        return self.data


@dataclass(frozen=True)
class GenerateRequest:
    api_key: str
    endpoint_id: str
    image: bytes | None
    prompt: str | None
    resolution: int
    texture_size: int
    seed: int | None = None


@dataclass(frozen=True)
class SegmentRequest:
    api_key: str
    endpoint_id: str
    mesh: bytes


@dataclass(frozen=True)
class SegmentResult:
    parts: list[Asset]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RigRequest:
    api_key: str
    endpoint_id: str
    mesh: bytes
    seed: int | None = None


@dataclass(frozen=True)
class MotionRequest:
    api_key: str
    endpoint_id: str
    prompt: str
    character_fbx: bytes
    duration: float
    fps: int
    guidance_scale: float
    seed: int | None = None


@dataclass(frozen=True)
class MotionResult:
    animated_asset: Asset
    metadata: dict[str, Any] = field(default_factory=dict)


class Provider:
    """Base class for capability providers."""

    id: str
    name: str
    description: str = ""
    capabilities: frozenset[Capability] = frozenset()
    endpoint_pref_field: str | None = None

    def supports(self, capability: Capability) -> bool:
        return capability in self.capabilities

    def generate(self, req: GenerateRequest) -> Asset:
        raise NotImplementedError

    def segment(self, req: SegmentRequest) -> SegmentResult:
        raise NotImplementedError

    def rig(self, req: RigRequest) -> Asset:
        raise NotImplementedError

    def motion(self, req: MotionRequest) -> MotionResult:
        raise NotImplementedError
