"""Tests for the Meshy provider request/response mapping."""

import importlib
import unittest
from unittest.mock import patch

from meshmaker import api

base = importlib.import_module("meshmaker.providers.base")
common = importlib.import_module("meshmaker.providers.common")
meshy = importlib.import_module("meshmaker.providers.meshy")


class TestMeshyParams(unittest.TestCase):
    def test_controls(self):
        params = meshy.MeshyProvider().params
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


class TestMeshyProvider(unittest.TestCase):
    def setUp(self):
        self.provider = meshy.MeshyProvider()
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

        with patch.object(api, "http_post_json", return_value=created) as mock_post, \
                patch.object(api, "http_get_json", return_value=task) as mock_get:
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
        with patch.object(api, "http_post_json", return_value=created) as mock_post, \
                patch.object(api, "http_get_json", return_value=task):
            self.provider.generate(req)
        self.assertTrue(mock_post.call_args.args[1]["should_remesh"])

    def test_polls_until_succeeded(self):
        created = {"result": "t1"}
        get_responses = [
            {"status": "PENDING"},
            {"status": "IN_PROGRESS"},
            {"status": "SUCCEEDED", "model_urls": {"glb": "https://m/model.glb"}},
        ]
        with patch.object(api, "http_post_json", return_value=created), \
                patch.object(api, "http_get_json", side_effect=get_responses), \
                patch("time.sleep"):
            asset = self.provider.generate(self.req)
        self.assertEqual(asset.url, "https://m/model.glb")

    def test_failed_task_raises(self):
        created = {"result": "t1"}
        task = {"status": "FAILED", "task_error": {"message": "bad image"}}
        with patch.object(api, "http_post_json", return_value=created), \
                patch.object(api, "http_get_json", return_value=task):
            with self.assertRaises(common.ProviderError) as ctx:
                self.provider.generate(self.req)
        self.assertIn("bad image", str(ctx.exception))

    def test_no_task_id_raises(self):
        with patch.object(api, "http_post_json", return_value={}):
            with self.assertRaises(common.ProviderError):
                self.provider.generate(self.req)


if __name__ == "__main__":
    unittest.main()
