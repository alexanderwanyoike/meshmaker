"""Per-provider generation controls.

Each provider declares a ``params`` schema (tuple of ParamSpec). This module
turns those schemas into Blender PropertyGroups at register time, draws the
controls for the active provider, and collects their values into the ``params``
dict passed to ``provider.generate``. Adding a provider with new controls needs
no UI code here - it is driven entirely off the schema.
"""

import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, PointerProperty
from bpy.types import PropertyGroup

from ..providers import registry

_INT32_MAX = 2_147_483_647

_pg_classes = []
_prop_names = {}  # provider.id -> WindowManager property name


def _annotation_for(spec):
    if spec.kind == "int":
        return IntProperty(
            name=spec.label,
            description=spec.description,
            default=spec.default,
            min=spec.min if spec.min is not None else -_INT32_MAX,
            max=spec.max if spec.max is not None else _INT32_MAX,
        )
    if spec.kind == "bool":
        return BoolProperty(
            name=spec.label,
            description=spec.description,
            default=spec.default,
        )
    if spec.kind == "enum":
        items = [(value, label, "") for value, label in spec.items]
        return EnumProperty(
            name=spec.label,
            description=spec.description,
            items=items,
            default=spec.default,
        )
    raise ValueError(f"Unknown ParamSpec kind: {spec.kind}")


def _prop_name(provider):
    return f"meshmaker_params_{provider.id.lower()}"


def register():
    for provider in registry.list_providers():
        if not provider.params:
            continue
        annotations = {spec.key: _annotation_for(spec) for spec in provider.params}
        cls = type(
            f"MESHMAKER_PG_{provider.id}",
            (PropertyGroup,),
            {"__annotations__": annotations},
        )
        bpy.utils.register_class(cls)
        _pg_classes.append(cls)

        name = _prop_name(provider)
        setattr(bpy.types.WindowManager, name, PointerProperty(type=cls))
        _prop_names[provider.id] = name


def unregister():
    for name in _prop_names.values():
        if hasattr(bpy.types.WindowManager, name):
            delattr(bpy.types.WindowManager, name)
    _prop_names.clear()
    for cls in reversed(_pg_classes):
        bpy.utils.unregister_class(cls)
    _pg_classes.clear()


def _settings(wm, provider):
    return getattr(wm, _prop_names[provider.id], None)


def draw(layout, wm, provider):
    """Draw the active provider's controls."""
    settings = _settings(wm, provider)
    if settings is None:
        return
    col = layout.column(align=True)
    for spec in provider.params:
        col.prop(settings, spec.key)


def collect(wm, provider):
    """Read the active provider's control values into a params dict."""
    settings = _settings(wm, provider)
    if settings is None:
        return {}
    return {spec.key: getattr(settings, spec.key) for spec in provider.params}
