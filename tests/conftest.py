"""Shared setup for the provider test suite.

``meshmaker/__init__.py`` imports ``bpy``, which isn't available off Blender. The
provider modules don't need ``bpy``, so we register lightweight stand-in
``meshmaker`` / ``meshmaker.providers`` packages and a mock ``meshmaker.api``
before any test imports a provider module. This runs at conftest import, before
test collection, so plain ``import meshmaker.providers.*`` works in the tests.
"""

import os
import sys
import types
from unittest.mock import Mock

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_MESHMAKER_DIR = os.path.join(_ROOT, "meshmaker")
_PROVIDERS_DIR = os.path.join(_MESHMAKER_DIR, "providers")


def _install_fake_meshmaker_package():
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
