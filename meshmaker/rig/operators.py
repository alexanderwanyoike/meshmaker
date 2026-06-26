"""Blender operators for RigMaker."""

import os
import tempfile
import threading
import time

import bpy
from bpy.props import IntProperty, StringProperty
from bpy.types import Operator

from .. import ADDON_ID
from ..providers import registry
from ..providers.base import Capability, RigRequest


def _apply_rig(context, fbx_bytes, original_obj):
    """Import MIA FBX (Mixamo skeleton + correct weights), hide original mesh."""
    existing = set(bpy.data.objects)

    # Write FBX to temp file and import
    tmp = tempfile.NamedTemporaryFile(suffix=".fbx", delete=False)
    try:
        tmp.write(fbx_bytes)
        tmp.close()
        bpy.ops.import_scene.fbx(filepath=tmp.name)
    finally:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    new_objects = set(bpy.data.objects) - existing
    if not new_objects:
        raise RuntimeError("FBX import produced no objects")

    armature = next((o for o in new_objects if o.type == 'ARMATURE'), None)
    if armature is None:
        for o in new_objects:
            bpy.data.objects.remove(o, do_unlink=True)
        raise RuntimeError("No armature in FBX")

    # Apply transforms on all imported objects so scale/rotation
    # offsets are baked into geometry — prevents multi-part meshes
    # (e.g. armor pieces) from scattering.
    bpy.ops.object.select_all(action='DESELECT')
    for o in new_objects:
        o.select_set(True)
    context.view_layer.objects.active = armature
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # MIA's output mesh has correct weights — hide original
    original_obj.hide_set(True)
    original_obj.hide_render = True

    bpy.ops.object.select_all(action='DESELECT')
    armature.select_set(True)
    context.view_layer.objects.active = armature
    return armature


class RIGMAKER_OT_auto_rig(Operator):
    bl_idname = "rigmaker.auto_rig"
    bl_label = "Auto Rig"
    bl_description = "Send mesh to Make It Animatable for automatic Mixamo rigging"

    _thread = None
    _result = None
    _error = None
    _timer = None
    _start_time = None
    _original_obj_name = None

    def execute(self, context):
        prefs = context.preferences.addons[ADDON_ID].preferences
        api_key = prefs.runpod_api_key
        endpoint_id = prefs.mia_endpoint_id
        provider = registry.resolve(Capability.RIG, "MIA")

        if not api_key:
            self.report({'ERROR'}, "RunPod API key not set. Check addon preferences.")
            return {'CANCELLED'}
        if not endpoint_id:
            self.report({'ERROR'}, "MIA endpoint ID not set. Check addon preferences.")
            return {'CANCELLED'}

        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object first.")
            return {'CANCELLED'}
        if not obj.select_get():
            self.report({'ERROR'}, "Mesh is not selected in the viewport.")
            return {'CANCELLED'}

        # Export selected mesh as GLB
        tmp = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
        tmp.close()
        try:
            bpy.ops.export_scene.gltf(
                filepath=tmp.name,
                export_format='GLB',
                use_selection=True,
            )
            with open(tmp.name, "rb") as f:
                mesh_bytes = f.read()
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

        wm = context.window_manager
        seed = wm.rigmaker_seed

        request = RigRequest(
            api_key=api_key,
            endpoint_id=endpoint_id,
            mesh=mesh_bytes,
            seed=seed if seed > 0 else None,
        )

        # Reset state
        cls = RIGMAKER_OT_auto_rig
        cls._thread = None
        cls._result = None
        cls._error = None
        cls._start_time = time.monotonic()
        cls._original_obj_name = obj.name

        wm.rigmaker_status = "Rigging mesh..."

        def run():
            try:
                result = provider.rig(request)
                cls._result = result
            except Exception as e:
                cls._error = str(e)

        cls._thread = threading.Thread(target=run, daemon=True)
        cls._thread.start()

        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        wm = context.window_manager
        cls = RIGMAKER_OT_auto_rig
        thread = cls._thread

        # Still running
        if thread is not None and thread.is_alive():
            return {'PASS_THROUGH'}

        # Done — clean up timer
        wm.event_timer_remove(self._timer)
        self._timer = None

        # Check for errors
        error = cls._error
        if error:
            wm.rigmaker_status = f"Error: {error[:80]}"
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        # Extract FBX
        asset = cls._result
        if asset is None:
            wm.rigmaker_status = "Error: no FBX in response"
            self.report({'ERROR'}, "No FBX data in response")
            return {'CANCELLED'}

        fbx_bytes = asset.require_data()

        # Look up original object by name
        original_obj = bpy.data.objects.get(cls._original_obj_name)
        if original_obj is None:
            wm.rigmaker_status = "Error: original mesh deleted"
            self.report({'ERROR'}, "Original mesh object was deleted during processing")
            return {'CANCELLED'}

        # Apply the rig
        try:
            armature = _apply_rig(context, fbx_bytes, original_obj)
        except Exception as e:
            wm.rigmaker_status = f"Error: {str(e)[:60]}"
            self.report({'ERROR'}, f"Failed to apply rig: {e}")
            return {'CANCELLED'}

        elapsed = time.monotonic() - cls._start_time
        bone_count = len(armature.data.bones)
        seed_val = asset.metadata.get("seed", "n/a")
        wm.rigmaker_status = f"Done ({bone_count} bones, {elapsed:.0f}s, seed={seed_val})"
        self.report({'INFO'}, f"Rig applied: {bone_count} bones")

        return {'FINISHED'}

    def cancel(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None


def register():
    bpy.utils.register_class(RIGMAKER_OT_auto_rig)

    wm = bpy.types.WindowManager
    wm.rigmaker_status = StringProperty(name="Status", default="Idle")
    wm.rigmaker_seed = IntProperty(
        name="Seed",
        description="Random seed (0 = random)",
        default=0,
        min=0,
    )


def unregister():
    wm = bpy.types.WindowManager
    del wm.rigmaker_seed
    del wm.rigmaker_status

    bpy.utils.unregister_class(RIGMAKER_OT_auto_rig)
