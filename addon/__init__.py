bl_info = {
    "name": "CharMaker",
    "author": "CharMaker",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > CharMaker",
    "description": "Generate concept art with Gemini and 3D meshes with Trellis 2",
    "category": "3D View",
}

from . import preferences, operators, panels


def register():
    preferences.register()
    operators.register()
    panels.register()


def unregister():
    panels.unregister()
    operators.unregister()
    preferences.unregister()
