"""Tests for the Generate provider registry."""

import importlib
import unittest

registry = importlib.import_module("meshmaker.providers.registry")


class TestProviderRegistry(unittest.TestCase):
    def test_lists_generate_providers(self):
        ids = [provider.id for provider in registry.list_providers()]
        self.assertEqual(
            ids,
            ["FAL_HUNYUAN3D", "FAL_PIXAL3D", "FAL_TRIPO", "FAL_RODIN", "MESHY"],
        )

    def test_resolve_default_is_first(self):
        self.assertEqual(registry.resolve().id, "FAL_HUNYUAN3D")

    def test_resolves_specific_provider(self):
        self.assertEqual(registry.resolve("MESHY").id, "MESHY")

    def test_unknown_provider_raises(self):
        with self.assertRaises(LookupError):
            registry.resolve("NOPE")


if __name__ == "__main__":
    unittest.main()
