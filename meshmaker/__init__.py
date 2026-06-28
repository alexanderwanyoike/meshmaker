bl_info = {
    "name": "MeshMaker",
    "author": "MeshMaker",
    "version": (0, 4, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar",
    "description": "Generate 3D meshes from images via hosted AI providers (Fal, Meshy)",
    "category": "3D View",
}

ADDON_ID = __name__

from . import preferences
from .mesh import operators as mesh_ops, panels as mesh_panels, params as mesh_params


def register():
    preferences.register()
    mesh_params.register()
    mesh_ops.register()
    mesh_panels.register()


def unregister():
    mesh_panels.unregister()
    mesh_ops.unregister()
    mesh_params.unregister()
    preferences.unregister()
