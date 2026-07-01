"""Tests for the Fal-hosted providers (Hunyuan3D, Pixal3D, Tripo, Rodin).

All four share the queue transport in ``providers/fal/queue.py``; each test
mocks the shared ``meshmaker.api`` HTTP layer and asserts the request shape and
the response -> ``Asset`` mapping.
"""

import importlib
import unittest
from unittest.mock import patch

from meshmaker import api

base = importlib.import_module("meshmaker.providers.base")
common = importlib.import_module("meshmaker.providers.common")
fal = importlib.import_module("meshmaker.providers.fal")


class TestFalParams(unittest.TestCase):
    def test_hunyuan_controls(self):
        params = fal.FalHunyuan3DProvider().params
        keys = [s.key for s in params]
        self.assertIn("tier", keys)
        self.assertIn("generate_type", keys)
        # Fal cannot honestly go below its 40k API floor.
        face_count = next(s for s in params if s.key == "face_count")
        self.assertEqual(face_count.min, 40000)

    def test_pixal3d_controls(self):
        params = fal.FalPixal3DProvider().params
        keys = [s.key for s in params]
        for key in ("resolution", "texture_size", "remesh", "decimation_target"):
            self.assertIn(key, keys)
        resolution = next(s for s in params if s.key == "resolution")
        self.assertEqual([v for v, _ in resolution.items], ["1024", "1536"])

    def test_tripo_controls(self):
        keys = [s.key for s in fal.FalTripoProvider().params]
        for key in ("texture", "pbr", "quad", "face_limit"):
            self.assertIn(key, keys)

    def test_rodin_controls(self):
        keys = [s.key for s in fal.FalRodinProvider().params]
        for key in ("quality", "material", "tier", "hyper_mode"):
            self.assertIn(key, keys)

    def test_all_fal_providers_share_one_key(self):
        for cls in (
            fal.FalHunyuan3DProvider,
            fal.FalPixal3DProvider,
            fal.FalTripoProvider,
            fal.FalRodinProvider,
        ):
            self.assertEqual(cls().api_key_pref_field, "fal_api_key")


class TestFalHunyuan3DProvider(unittest.TestCase):
    def setUp(self):
        self.provider = fal.FalHunyuan3DProvider()
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

        with patch.object(api, "http_post_json", return_value=submit) as mock_post, \
                patch.object(api, "http_get_json", side_effect=[status, result]):
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
        with patch.object(api, "http_post_json", return_value=submit) as mock_post, \
                patch.object(api, "http_get_json", side_effect=[{"status": "COMPLETED"}, result]):
            self.provider.generate(self.req)
        self.assertEqual(
            mock_post.call_args.args[0],
            "https://queue.fal.run/fal-ai/hunyuan-3d/v3.1/rapid/image-to-3d",
        )

    def test_generate_falls_back_to_model_urls(self):
        submit = {"status_url": "s", "response_url": "r"}
        result = {"model_urls": {"glb": {"url": "https://fal.media/alt.glb"}}}
        with patch.object(api, "http_post_json", return_value=submit), \
                patch.object(api, "http_get_json", side_effect=[{"status": "COMPLETED"}, result]):
            asset = self.provider.generate(self.req)
        self.assertEqual(asset.url, "https://fal.media/alt.glb")

    def test_prefers_model_urls_glb_over_polymorphic_model_glb(self):
        # model_glb can point at an OBJ on some tiers; model_urls.glb must win.
        submit = {"status_url": "s", "response_url": "r"}
        result = {
            "model_glb": {"url": "https://fal.media/model.obj"},
            "model_urls": {"glb": {"url": "https://fal.media/model.glb"}},
        }
        with patch.object(api, "http_post_json", return_value=submit), \
                patch.object(api, "http_get_json", side_effect=[{"status": "COMPLETED"}, result]):
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
        with patch.object(api, "http_post_json", return_value=submit), \
                patch.object(api, "http_get_json", side_effect=get_responses), \
                patch("time.sleep"):
            asset = self.provider.generate(self.req)
        self.assertEqual(asset.url, "https://fal.media/model.glb")

    def test_missing_queue_urls_raises(self):
        with patch.object(api, "http_post_json", return_value={}):
            with self.assertRaises(common.ProviderError):
                self.provider.generate(self.req)

    def test_no_glb_url_raises(self):
        submit = {"status_url": "s", "response_url": "r"}
        with patch.object(api, "http_post_json", return_value=submit), \
                patch.object(api, "http_get_json", side_effect=[{"status": "COMPLETED"}, {}]):
            with self.assertRaises(common.ProviderError):
                self.provider.generate(self.req)


class TestFalPixal3DProvider(unittest.TestCase):
    def setUp(self):
        self.provider = fal.FalPixal3DProvider()
        self.req = base.GenerateRequest(
            api_key="fal-key",
            image=b"image-bytes",
            params={
                "resolution": "1536",
                "texture_size": "4096",
                "remesh": True,
                "decimation_target": 100000,
            },
        )

    def test_generate_maps_request_and_response(self):
        submit = {"status_url": "s", "response_url": "r"}
        result = {"model_glb": {"url": "https://fal.media/pixal.glb"}, "seed": 7}
        with patch.object(api, "http_post_json", return_value=submit) as mock_post, \
                patch.object(api, "http_get_json", side_effect=[{"status": "COMPLETED"}, result]):
            asset = self.provider.generate(self.req)

        self.assertEqual(asset.url, "https://fal.media/pixal.glb")
        self.assertEqual(asset.metadata["provider"], "FAL_PIXAL3D")

        url, payload, _ = mock_post.call_args.args[:3]
        self.assertEqual(url, "https://queue.fal.run/fal-ai/pixal3d")
        self.assertTrue(payload["image_url"].startswith("data:image/png;base64,"))
        # Enum values arrive as strings; the payload must send real ints.
        self.assertEqual(payload["resolution"], 1536)
        self.assertEqual(payload["texture_size"], 4096)
        self.assertEqual(payload["decimation_target"], 100000)


class TestFalTripoProvider(unittest.TestCase):
    def setUp(self):
        self.provider = fal.FalTripoProvider()
        self.req = base.GenerateRequest(
            api_key="fal-key",
            image=b"image-bytes",
            params={"texture": "HD", "pbr": True, "quad": True, "face_limit": 40000},
        )

    def test_generate_maps_request_and_response(self):
        submit = {"status_url": "s", "response_url": "r"}
        # Tripo nests the GLB under model_mesh.url.
        result = {"model_mesh": {"url": "https://fal.media/tripo.glb"}}
        with patch.object(api, "http_post_json", return_value=submit) as mock_post, \
                patch.object(api, "http_get_json", side_effect=[{"status": "COMPLETED"}, result]):
            asset = self.provider.generate(self.req)

        self.assertEqual(asset.url, "https://fal.media/tripo.glb")
        self.assertEqual(asset.metadata["provider"], "FAL_TRIPO")

        url, payload, _ = mock_post.call_args.args[:3]
        self.assertEqual(url, "https://queue.fal.run/tripo3d/tripo/v2.5/image-to-3d")
        self.assertTrue(payload["image_url"].startswith("data:image/png;base64,"))
        self.assertEqual(payload["texture"], "HD")
        self.assertTrue(payload["pbr"])
        self.assertTrue(payload["quad"])
        self.assertEqual(payload["face_limit"], 40000)


class TestFalRodinProvider(unittest.TestCase):
    def setUp(self):
        self.provider = fal.FalRodinProvider()
        self.req = base.GenerateRequest(
            api_key="fal-key",
            image=b"image-bytes",
            params={"quality": "high", "material": "PBR", "tier": "Regular", "hyper_mode": True},
        )

    def test_generate_maps_request_and_response(self):
        submit = {"status_url": "s", "response_url": "r"}
        result = {"model_mesh": {"url": "https://fal.media/rodin.glb"}}
        with patch.object(api, "http_post_json", return_value=submit) as mock_post, \
                patch.object(api, "http_get_json", side_effect=[{"status": "COMPLETED"}, result]):
            asset = self.provider.generate(self.req)

        self.assertEqual(asset.url, "https://fal.media/rodin.glb")
        self.assertEqual(asset.metadata["provider"], "FAL_RODIN")

        url, payload, _ = mock_post.call_args.args[:3]
        self.assertEqual(url, "https://queue.fal.run/fal-ai/hyper3d/rodin")
        # Rodin takes an array of image urls.
        self.assertEqual(len(payload["input_image_urls"]), 1)
        self.assertTrue(payload["input_image_urls"][0].startswith("data:image/png;base64,"))
        self.assertEqual(payload["geometry_file_format"], "glb")
        self.assertEqual(payload["quality"], "high")
        self.assertTrue(payload["hyper_mode"])


if __name__ == "__main__":
    unittest.main()
