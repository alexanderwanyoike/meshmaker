"""RunPod-backed providers for current MeshMaker handlers."""

import base64
from typing import Any

from .. import api
from .base import (
    Asset,
    Capability,
    GenerateRequest,
    MotionRequest,
    MotionResult,
    Provider,
    RigRequest,
    SegmentRequest,
    SegmentResult,
)


def _decode_asset(data: str, fmt: str, metadata: dict[str, Any] | None = None,
                  name: str | None = None) -> Asset:
    return Asset(
        format=fmt,
        data=base64.b64decode(data),
        metadata=metadata or {},
        name=name,
    )


class RunPodGenerateProvider(Provider):
    capabilities = frozenset({Capability.GENERATE})

    def __init__(
        self,
        provider_id: str,
        name: str,
        description: str,
        endpoint_pref_field: str,
        supports_text: bool,
        supports_image: bool = True,
    ):
        self.id = provider_id
        self.name = name
        self.description = description
        self.endpoint_pref_field = endpoint_pref_field
        self.supports_text = supports_text
        self.supports_image = supports_image

    def generate(self, req: GenerateRequest) -> Asset:
        payload_input: dict[str, Any] = {
            "resolution": req.resolution,
            "texture_size": req.texture_size,
        }
        if req.image is not None:
            payload_input["image"] = base64.b64encode(req.image).decode("utf-8")
        if req.prompt:
            payload_input["text"] = req.prompt
        if req.seed is not None and req.seed > 0:
            payload_input["seed"] = req.seed

        result = api.call_runpod(req.api_key, req.endpoint_id, {"input": payload_input})
        glb_b64 = result.get("glb")
        if not glb_b64:
            raise ValueError("No GLB data in RunPod response")
        return _decode_asset(glb_b64, "glb", result.get("metadata", {}))


class RunPodMIAProvider(Provider):
    id = "MIA"
    name = "MIA"
    description = "Make It Animatable Mixamo rigging"
    endpoint_pref_field = "mia_endpoint_id"
    capabilities = frozenset({Capability.RIG})

    def rig(self, req: RigRequest) -> Asset:
        payload_input: dict[str, Any] = {
            "mesh": base64.b64encode(req.mesh).decode("utf-8"),
        }
        if req.seed is not None and req.seed > 0:
            payload_input["seed"] = req.seed

        result = api.call_runpod(req.api_key, req.endpoint_id, {"input": payload_input})
        fbx_b64 = result.get("output")
        if not fbx_b64:
            raise ValueError("No FBX data in RunPod response")
        metadata = {
            key: value
            for key, value in result.items()
            if key not in {"output"}
        }
        return _decode_asset(fbx_b64, "fbx", metadata)


class RunPodHYMotionProvider(Provider):
    id = "HYMOTION"
    name = "HY-Motion"
    description = "HY-Motion text-to-animation"
    endpoint_pref_field = "hymotion_endpoint_id"
    capabilities = frozenset({Capability.MOTION})

    def motion(self, req: MotionRequest) -> MotionResult:
        payload_input: dict[str, Any] = {
            "prompt": req.prompt,
            "character_fbx": base64.b64encode(req.character_fbx).decode("utf-8"),
            "duration": req.duration,
            "fps": req.fps,
            "guidance_scale": req.guidance_scale,
        }
        if req.seed is not None and req.seed > 0:
            payload_input["seed"] = req.seed

        result = api.call_runpod(req.api_key, req.endpoint_id, {"input": payload_input})
        animated_fbx_b64 = result.get("animated_fbx")
        if not animated_fbx_b64:
            raise ValueError("No animated FBX data in RunPod response")

        metadata = result.get("metadata", {})
        return MotionResult(
            animated_asset=_decode_asset(animated_fbx_b64, "fbx", metadata),
            metadata=metadata,
        )


class RunPodP3SAMProvider(Provider):
    id = "P3SAM"
    name = "Hunyuan3D-Part"
    description = "P3-SAM part segmentation"
    endpoint_pref_field = "segment_endpoint_id"
    capabilities = frozenset({Capability.SEGMENT})

    def segment(self, req: SegmentRequest) -> SegmentResult:
        payload = {
            "input": {
                "mesh": base64.b64encode(req.mesh).decode("utf-8"),
            },
        }
        result = api.call_runpod(req.api_key, req.endpoint_id, payload)
        parts = []
        for idx, part in enumerate(result.get("parts", [])):
            part_b64 = part.get("mesh")
            if not part_b64:
                continue
            metadata = {
                key: value
                for key, value in part.items()
                if key not in {"mesh", "name"}
            }
            parts.append(
                _decode_asset(
                    part_b64,
                    "glb",
                    metadata,
                    part.get("name", f"part_{idx}"),
                )
            )

        if not parts:
            raise ValueError("No segmented parts in RunPod response")
        return SegmentResult(parts=parts, metadata=result.get("metadata", {}))


TRELLIS2 = RunPodGenerateProvider(
    provider_id="TRELLIS2",
    name="Trellis 2",
    description="Microsoft TRELLIS.2-4B image-to-3D",
    endpoint_pref_field="trellis_endpoint_id",
    supports_text=False,
)

HUNYUAN3D = RunPodGenerateProvider(
    provider_id="HUNYUAN3D",
    name="Hunyuan3D 2.1",
    description="Tencent Hunyuan3D 2.1 image-to-3D",
    endpoint_pref_field="hunyuan3d_endpoint_id",
    supports_text=False,
)

MIA = RunPodMIAProvider()
HYMOTION = RunPodHYMotionProvider()
P3SAM = RunPodP3SAMProvider()
