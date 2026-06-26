"""Tests for provider request/response mapping."""

import base64
import importlib
import os
import sys
import types
import unittest
from unittest.mock import Mock, patch


_ROOT = os.path.join(os.path.dirname(__file__), "..")
_MESHMaker_DIR = os.path.join(_ROOT, "meshmaker")
_PROVIDERS_DIR = os.path.join(_MESHMaker_DIR, "providers")


def _install_fake_meshmaker_package():
    """Load provider modules without importing meshmaker/__init__.py and bpy."""
    for name in list(sys.modules):
        if name == "meshmaker" or name.startswith("meshmaker."):
            del sys.modules[name]

    meshmaker_pkg = types.ModuleType("meshmaker")
    meshmaker_pkg.__path__ = [_MESHMaker_DIR]
    sys.modules["meshmaker"] = meshmaker_pkg

    providers_pkg = types.ModuleType("meshmaker.providers")
    providers_pkg.__path__ = [_PROVIDERS_DIR]
    sys.modules["meshmaker.providers"] = providers_pkg

    api_module = types.ModuleType("meshmaker.api")
    api_module.call_runpod = Mock()
    sys.modules["meshmaker.api"] = api_module
    meshmaker_pkg.api = api_module


_install_fake_meshmaker_package()
base = importlib.import_module("meshmaker.providers.base")
runpod = importlib.import_module("meshmaker.providers.runpod")
registry = importlib.import_module("meshmaker.providers.registry")


class TestProviderRegistry(unittest.TestCase):
    def test_lists_generate_providers(self):
        providers = registry.providers_for(base.Capability.GENERATE)
        self.assertEqual([provider.id for provider in providers], ["TRELLIS2", "HUNYUAN3D"])

    def test_resolves_specific_provider(self):
        provider = registry.resolve(base.Capability.RIG, "MIA")
        self.assertEqual(provider.name, "MIA")

    def test_unknown_provider_raises(self):
        with self.assertRaises(LookupError):
            registry.resolve(base.Capability.GENERATE, "NOPE")


class TestRunPodProviders(unittest.TestCase):
    def _patch_runpod(self, response):
        return patch.object(runpod.api, "call_runpod", return_value=response)

    def test_generate_maps_request_and_decodes_asset(self):
        glb_bytes = b"glb-data"
        response = {
            "glb": base64.b64encode(glb_bytes).decode("utf-8"),
            "metadata": {"seed": 123},
        }
        req = base.GenerateRequest(
            api_key="key",
            endpoint_id="endpoint",
            image=b"image-data",
            prompt=None,
            resolution=512,
            texture_size=2048,
            seed=123,
        )

        with self._patch_runpod(response) as mock_call:
            asset = runpod.TRELLIS2.generate(req)

        self.assertEqual(asset.format, "glb")
        self.assertEqual(asset.require_data(), glb_bytes)
        self.assertEqual(asset.metadata, {"seed": 123})

        payload = mock_call.call_args.args[2]
        self.assertEqual(mock_call.call_args.args[:2], ("key", "endpoint"))
        self.assertEqual(payload["input"]["resolution"], 512)
        self.assertEqual(payload["input"]["texture_size"], 2048)
        self.assertEqual(payload["input"]["seed"], 123)
        self.assertEqual(
            base64.b64decode(payload["input"]["image"]),
            b"image-data",
        )
        self.assertNotIn("text", payload["input"])

    def test_rig_maps_output_asset(self):
        fbx_bytes = b"fbx-data"
        response = {
            "output": base64.b64encode(fbx_bytes).decode("utf-8"),
            "seed": 7,
            "processing_time": 1.5,
        }
        req = base.RigRequest(
            api_key="key",
            endpoint_id="endpoint",
            mesh=b"mesh-data",
            seed=7,
        )

        with self._patch_runpod(response) as mock_call:
            asset = runpod.MIA.rig(req)

        self.assertEqual(asset.format, "fbx")
        self.assertEqual(asset.require_data(), fbx_bytes)
        self.assertEqual(asset.metadata["seed"], 7)

        payload = mock_call.call_args.args[2]
        self.assertEqual(base64.b64decode(payload["input"]["mesh"]), b"mesh-data")
        self.assertEqual(payload["input"]["seed"], 7)

    def test_motion_maps_animated_asset(self):
        fbx_bytes = b"animated"
        response = {
            "animated_fbx": base64.b64encode(fbx_bytes).decode("utf-8"),
            "metadata": {"num_frames": 90, "fps": 30},
        }
        req = base.MotionRequest(
            api_key="key",
            endpoint_id="endpoint",
            prompt="walk",
            character_fbx=b"character",
            duration=3.0,
            fps=30,
            guidance_scale=7.5,
            seed=None,
        )

        with self._patch_runpod(response) as mock_call:
            result = runpod.HYMOTION.motion(req)

        self.assertEqual(result.animated_asset.format, "fbx")
        self.assertEqual(result.animated_asset.require_data(), fbx_bytes)
        self.assertEqual(result.metadata["num_frames"], 90)

        payload = mock_call.call_args.args[2]
        self.assertEqual(payload["input"]["prompt"], "walk")
        self.assertEqual(base64.b64decode(payload["input"]["character_fbx"]), b"character")
        self.assertNotIn("seed", payload["input"])

    def test_segment_maps_parts(self):
        part_a = base64.b64encode(b"part-a").decode("utf-8")
        part_b = base64.b64encode(b"part-b").decode("utf-8")
        response = {
            "parts": [
                {"name": "head", "mesh": part_a, "face_count": 10},
                {"name": "body", "mesh": part_b, "face_count": 20},
            ],
            "metadata": {"num_parts": 2},
        }
        req = base.SegmentRequest(
            api_key="key",
            endpoint_id="endpoint",
            mesh=b"mesh-data",
        )

        with self._patch_runpod(response) as mock_call:
            result = runpod.P3SAM.segment(req)

        self.assertEqual([part.name for part in result.parts], ["head", "body"])
        self.assertEqual(result.parts[0].require_data(), b"part-a")
        self.assertEqual(result.parts[1].metadata["face_count"], 20)
        self.assertEqual(result.metadata["num_parts"], 2)

        payload = mock_call.call_args.args[2]
        self.assertEqual(base64.b64decode(payload["input"]["mesh"]), b"mesh-data")


if __name__ == "__main__":
    unittest.main()
