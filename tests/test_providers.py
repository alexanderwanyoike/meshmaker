"""Tests for Generate provider request/response mapping (Fal, Meshy)."""

import importlib
import os
import sys
import types
import unittest
from unittest.mock import Mock, patch


_ROOT = os.path.join(os.path.dirname(__file__), "..")
_MESHMAKER_DIR = os.path.join(_ROOT, "meshmaker")
_PROVIDERS_DIR = os.path.join(_MESHMAKER_DIR, "providers")


def _install_fake_meshmaker_package():
    """Load provider modules without importing meshmaker/__init__.py and bpy."""
    for name in list(sys.modules):
        if name == "meshmaker" or name.startswith("meshmaker."):
            del sys.modules[name]

    meshmaker_pkg = types.ModuleType("meshmaker")
    meshmaker_pkg.__path__ = [_MESHMAKER_DIR]
    sys.modules["meshmaker"] = meshmaker_pkg

    providers_pkg = types.ModuleType("meshmaker.providers")
    providers_pkg.__path__ = [_PROVIDERS_DIR]
    sys.modules["meshmaker.providers"] = providers_pkg

    api_module = types.ModuleType("meshmaker.api")
    api_module.http_post_json = Mock()
    api_module.http_get_json = Mock()
    api_module.download = Mock()
    sys.modules["meshmaker.api"] = api_module
    meshmaker_pkg.api = api_module


_install_fake_meshmaker_package()
base = importlib.import_module("meshmaker.providers.base")
cloud = importlib.import_module("meshmaker.providers.cloud")
registry = importlib.import_module("meshmaker.providers.registry")


class TestProviderRegistry(unittest.TestCase):
    def test_lists_generate_providers(self):
        ids = [provider.id for provider in registry.list_providers()]
        self.assertEqual(ids, ["FAL_HUNYUAN3D", "MESHY"])

    def test_resolve_default_is_first(self):
        self.assertEqual(registry.resolve().id, "FAL_HUNYUAN3D")

    def test_resolves_specific_provider(self):
        self.assertEqual(registry.resolve("MESHY").id, "MESHY")

    def test_unknown_provider_raises(self):
        with self.assertRaises(LookupError):
            registry.resolve("NOPE")


class TestProviderParams(unittest.TestCase):
    def test_fal_controls(self):
        params = cloud.FalHunyuan3DProvider().params
        keys = [s.key for s in params]
        self.assertIn("tier", keys)
        self.assertIn("generate_type", keys)
        # Fal cannot honestly go below its 40k API floor.
        face_count = next(s for s in params if s.key == "face_count")
        self.assertEqual(face_count.min, 40000)

    def test_meshy_controls(self):
        params = cloud.MeshyProvider().params
        keys = [s.key for s in params]
        for key in ("should_remesh", "target_polycount", "topology", "should_texture", "enable_pbr"):
            self.assertIn(key, keys)
        # Remesh defaults on (so polycount applies); polycount floor is 25k.
        remesh = next(s for s in params if s.key == "should_remesh")
        self.assertTrue(remesh.default)
        polycount = next(s for s in params if s.key == "target_polycount")
        self.assertEqual(polycount.min, 25000)
        # symmetry_mode is deprecated/no-op on Meshy: no dead control.
        self.assertNotIn("symmetry_mode", keys)


class TestFalProvider(unittest.TestCase):
    def setUp(self):
        self.provider = cloud.FalHunyuan3DProvider()
        self.req = base.GenerateRequest(
            api_key="fal-key",
            image=b"image-bytes",
            params={
                "tier": "pro",
                "face_count": 60000,
                "generate_type": "Normal",
                "enable_pbr": True,
            },
        )

    def test_generate_maps_request_and_response(self):
        submit = {
            "status_url": "https://queue.fal.run/.../status",
            "response_url": "https://queue.fal.run/.../response",
        }
        status = {"status": "COMPLETED"}
        result = {"model_glb": {"url": "https://fal.media/model.glb"}, "seed": 42}

        with patch.object(cloud.api, "http_post_json", return_value=submit) as mock_post, \
                patch.object(cloud.api, "http_get_json", side_effect=[status, result]):
            asset = self.provider.generate(self.req)

        self.assertEqual(asset.url, "https://fal.media/model.glb")
        self.assertEqual(asset.format, "glb")
        self.assertEqual(asset.metadata["seed"], 42)
        self.assertEqual(asset.metadata["provider"], "FAL_HUNYUAN3D")

        url, payload, headers = mock_post.call_args.args[:3]
        self.assertEqual(url, "https://queue.fal.run/fal-ai/hunyuan-3d/v3.1/pro/image-to-3d")
        self.assertTrue(payload["input_image_url"].startswith("data:image/png;base64,"))
        self.assertEqual(payload["face_count"], 60000)
        self.assertEqual(payload["generate_type"], "Normal")
        self.assertTrue(payload["enable_pbr"])
        self.assertEqual(headers["Authorization"], "Key fal-key")

    def test_rapid_tier_changes_model_id(self):
        self.req.params["tier"] = "rapid"
        submit = {"status_url": "s", "response_url": "r"}
        result = {"model_glb": {"url": "https://fal.media/model.glb"}}
        with patch.object(cloud.api, "http_post_json", return_value=submit) as mock_post, \
                patch.object(cloud.api, "http_get_json", side_effect=[{"status": "COMPLETED"}, result]):
            self.provider.generate(self.req)
        self.assertEqual(
            mock_post.call_args.args[0],
            "https://queue.fal.run/fal-ai/hunyuan-3d/v3.1/rapid/image-to-3d",
        )

    def test_generate_falls_back_to_model_urls(self):
        submit = {"status_url": "s", "response_url": "r"}
        status = {"status": "COMPLETED"}
        result = {"model_urls": {"glb": {"url": "https://fal.media/alt.glb"}}}

        with patch.object(cloud.api, "http_post_json", return_value=submit), \
                patch.object(cloud.api, "http_get_json", side_effect=[status, result]):
            asset = self.provider.generate(self.req)

        self.assertEqual(asset.url, "https://fal.media/alt.glb")

    def test_prefers_model_urls_glb_over_polymorphic_model_glb(self):
        # model_glb can point at an OBJ on some tiers; model_urls.glb must win.
        submit = {"status_url": "s", "response_url": "r"}
        status = {"status": "COMPLETED"}
        result = {
            "model_glb": {"url": "https://fal.media/model.obj"},
            "model_urls": {"glb": {"url": "https://fal.media/model.glb"}},
        }

        with patch.object(cloud.api, "http_post_json", return_value=submit), \
                patch.object(cloud.api, "http_get_json", side_effect=[status, result]):
            asset = self.provider.generate(self.req)

        self.assertEqual(asset.url, "https://fal.media/model.glb")

    def test_polls_until_completed(self):
        submit = {"status_url": "s", "response_url": "r"}
        result = {"model_glb": {"url": "https://fal.media/model.glb"}}
        get_responses = [
            {"status": "IN_QUEUE"},
            {"status": "IN_PROGRESS"},
            {"status": "COMPLETED"},
            result,
        ]

        with patch.object(cloud.api, "http_post_json", return_value=submit), \
                patch.object(cloud.api, "http_get_json", side_effect=get_responses), \
                patch.object(cloud.time, "sleep"):
            asset = self.provider.generate(self.req)

        self.assertEqual(asset.url, "https://fal.media/model.glb")

    def test_missing_queue_urls_raises(self):
        with patch.object(cloud.api, "http_post_json", return_value={}):
            with self.assertRaises(cloud.ProviderError):
                self.provider.generate(self.req)

    def test_no_glb_url_raises(self):
        submit = {"status_url": "s", "response_url": "r"}
        with patch.object(cloud.api, "http_post_json", return_value=submit), \
                patch.object(cloud.api, "http_get_json", side_effect=[{"status": "COMPLETED"}, {}]):
            with self.assertRaises(cloud.ProviderError):
                self.provider.generate(self.req)


class TestMeshyProvider(unittest.TestCase):
    def setUp(self):
        self.provider = cloud.MeshyProvider()
        self.req = base.GenerateRequest(
            api_key="meshy-key",
            image=b"image-bytes",
            params={
                "ai_model": "meshy-6",
                "should_remesh": True,
                "target_polycount": 30000,
                "topology": "quad",
                "should_texture": True,
                "enable_pbr": False,
            },
        )

    def test_generate_maps_request_and_response(self):
        created = {"result": "task-123"}
        task = {
            "status": "SUCCEEDED",
            "model_urls": {"glb": "https://assets.meshy.ai/task-123/model.glb"},
            "consumed_credits": 30,
        }

        with patch.object(cloud.api, "http_post_json", return_value=created) as mock_post, \
                patch.object(cloud.api, "http_get_json", return_value=task) as mock_get:
            asset = self.provider.generate(self.req)

        self.assertEqual(asset.url, "https://assets.meshy.ai/task-123/model.glb")
        self.assertEqual(asset.metadata["task_id"], "task-123")
        self.assertEqual(asset.metadata["consumed_credits"], 30)

        url, payload, headers = mock_post.call_args.args[:3]
        self.assertEqual(url, "https://api.meshy.ai/openapi/v1/image-to-3d")
        self.assertTrue(payload["image_url"].startswith("data:image/png;base64,"))
        self.assertEqual(payload["ai_model"], "meshy-6")
        self.assertTrue(payload["should_remesh"])
        self.assertEqual(payload["target_polycount"], 30000)
        self.assertEqual(payload["topology"], "quad")
        self.assertTrue(payload["should_texture"])
        self.assertEqual(payload["target_formats"], ["glb"])
        self.assertEqual(headers["Authorization"], "Bearer meshy-key")

        # Poll URL includes the task id
        self.assertEqual(
            mock_get.call_args.args[0],
            "https://api.meshy.ai/openapi/v1/image-to-3d/task-123",
        )

    def test_should_remesh_defaults_on(self):
        # Without remesh, Meshy ignores target_polycount; the default must be True.
        req = base.GenerateRequest(api_key="k", image=b"img", params={})
        created = {"result": "t1"}
        task = {"status": "SUCCEEDED", "model_urls": {"glb": "https://m/x.glb"}}
        with patch.object(cloud.api, "http_post_json", return_value=created) as mock_post, \
                patch.object(cloud.api, "http_get_json", return_value=task):
            self.provider.generate(req)
        self.assertTrue(mock_post.call_args.args[1]["should_remesh"])

    def test_polls_until_succeeded(self):
        created = {"result": "t1"}
        get_responses = [
            {"status": "PENDING"},
            {"status": "IN_PROGRESS"},
            {"status": "SUCCEEDED", "model_urls": {"glb": "https://m/model.glb"}},
        ]
        with patch.object(cloud.api, "http_post_json", return_value=created), \
                patch.object(cloud.api, "http_get_json", side_effect=get_responses), \
                patch.object(cloud.time, "sleep"):
            asset = self.provider.generate(self.req)
        self.assertEqual(asset.url, "https://m/model.glb")

    def test_failed_task_raises(self):
        created = {"result": "t1"}
        task = {"status": "FAILED", "task_error": {"message": "bad image"}}
        with patch.object(cloud.api, "http_post_json", return_value=created), \
                patch.object(cloud.api, "http_get_json", return_value=task):
            with self.assertRaises(cloud.ProviderError) as ctx:
                self.provider.generate(self.req)
        self.assertIn("bad image", str(ctx.exception))

    def test_no_task_id_raises(self):
        with patch.object(cloud.api, "http_post_json", return_value={}):
            with self.assertRaises(cloud.ProviderError):
                self.provider.generate(self.req)


if __name__ == "__main__":
    unittest.main()
