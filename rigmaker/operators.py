"""Blender operators for RigMaker."""

import base64
import os
import tempfile
import threading
import time

import bpy
from bpy.props import IntProperty, StringProperty
from bpy.types import Operator

from . import api


def _apply_rig(context, fbx_bytes, original_obj):
    """Import FBX, transfer armature + weights to the original mesh, clean up."""
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

    # Find new objects
    new_objects = set(bpy.data.objects) - existing
    if not new_objects:
        raise RuntimeError("FBX import produced no objects")

    armature = None
    imported_meshes = []
    for obj in new_objects:
        if obj.type == 'ARMATURE':
            armature = obj
        elif obj.type == 'MESH':
            imported_meshes.append(obj)

    if armature is None:
        # Clean up imports before raising
        for obj in new_objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        raise RuntimeError("No armature found in FBX")

    if not imported_meshes:
        # Armature but no mesh to transfer from — still parent the armature
        pass

    # Parent original mesh to armature
    original_obj.parent = armature
    original_obj.matrix_parent_inverse = armature.matrix_world.inverted()

    # Add armature modifier
    arm_mod = original_obj.modifiers.new(name="Armature", type='ARMATURE')
    arm_mod.object = armature

    # Transfer vertex groups from imported mesh
    if imported_meshes:
        source_mesh = imported_meshes[0]

        # Create matching vertex groups on original mesh
        for vg in source_mesh.vertex_groups:
            if vg.name not in original_obj.vertex_groups:
                original_obj.vertex_groups.new(name=vg.name)

        # Data transfer modifier for weights
        dt_mod = original_obj.modifiers.new(name="WeightTransfer", type='DATA_TRANSFER')
        dt_mod.object = source_mesh
        dt_mod.use_vert_data = True
        dt_mod.data_types_verts = {'VGROUP_WEIGHTS'}
        dt_mod.vert_mapping = 'NEAREST'

        # Apply the data transfer modifier
        with context.temp_override(object=original_obj):
            bpy.ops.object.modifier_apply(modifier=dt_mod.name)

    # Clean up imported meshes (keep armature only)
    meshdata_to_remove = []
    for obj in imported_meshes:
        if obj.data:
            meshdata_to_remove.append(obj.data)
        bpy.data.objects.remove(obj, do_unlink=True)

    for md in meshdata_to_remove:
        if md.users == 0:
            bpy.data.meshes.remove(md)

    # Select original mesh + armature
    bpy.ops.object.select_all(action='DESELECT')
    original_obj.select_set(True)
    armature.select_set(True)
    context.view_layer.objects.active = original_obj

    return armature


class RIGMAKER_OT_auto_rig(Operator):
    bl_idname = "rigmaker.auto_rig"
    bl_label = "Auto Rig"
    bl_description = "Send mesh to UniRig for automatic rigging"

    _thread = None
    _result = None
    _error = None
    _timer = None
    _start_time = None
    _original_obj_name = None

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        api_key = prefs.runpod_api_key
        endpoint_id = prefs.unirig_endpoint_id

        if not api_key:
            self.report({'ERROR'}, "RunPod API key not set. Check addon preferences.")
            return {'CANCELLED'}
        if not endpoint_id:
            self.report({'ERROR'}, "UniRig endpoint ID not set. Check addon preferences.")
            return {'CANCELLED'}

        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object first.")
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
                mesh_b64 = base64.b64encode(f.read()).decode("utf-8")
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

        wm = context.window_manager
        seed = wm.rigmaker_seed

        payload_input = {"mesh": mesh_b64}
        if seed > 0:
            payload_input["seed"] = seed
        payload = {"input": payload_input}

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
                result = api.call_runpod(api_key, endpoint_id, payload)
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
        result = cls._result
        fbx_b64 = result.get("output") if result else None
        if not fbx_b64:
            wm.rigmaker_status = "Error: no FBX in response"
            self.report({'ERROR'}, "No FBX data in response")
            return {'CANCELLED'}

        fbx_bytes = base64.b64decode(fbx_b64)

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
        seed_val = result.get("seed", "n/a")
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
