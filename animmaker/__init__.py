bl_info = {
    "name": "AnimMaker",
    "author": "AnimMaker",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > AnimMaker",
    "description": "Text-to-animation via HY-Motion on RunPod",
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
