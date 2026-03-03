bl_info = {
    "name": "MeshMaker",
    "author": "MeshMaker",
    "version": (0, 2, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar",
    "description": "AI mesh pipeline: generate meshes, rig, animate, and segment parts",
    "category": "3D View",
}

ADDON_ID = __name__

from . import preferences
from .mesh import operators as mesh_ops, panels as mesh_panels
from .rig import operators as rig_ops, panels as rig_panels
from .anim import operators as anim_ops, panels as anim_panels
from .segment import operators as seg_ops, panels as seg_panels


def register():
    preferences.register()
    mesh_ops.register()
    mesh_panels.register()
    rig_ops.register()
    rig_panels.register()
    anim_ops.register()
    anim_panels.register()
    seg_ops.register()
    seg_panels.register()


def unregister():
    seg_panels.unregister()
    seg_ops.unregister()
    anim_panels.unregister()
    anim_ops.unregister()
    rig_panels.unregister()
    rig_ops.unregister()
    mesh_panels.unregister()
    mesh_ops.unregister()
    preferences.unregister()
