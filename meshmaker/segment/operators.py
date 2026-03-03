"""Blender operators for PartMaker part segmentation."""

import base64
import os
import tempfile
import threading
import time

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from .. import ADDON_ID, api


class SEGMENT_OT_segment_mesh(Operator):
    bl_idname = "segment.segment_mesh"
    bl_label = "Segment Parts"
    bl_description = "Segment mesh into parts via P3-SAM on RunPod"

    _thread = None
    _result = None
    _error = None
    _timer = None
    _start_time = None

    def execute(self, context):
        prefs = context.preferences.addons[ADDON_ID].preferences
        api_key = prefs.runpod_api_key
        endpoint_id = prefs.segment_endpoint_id

        if not api_key:
            self.report({'ERROR'}, "RunPod API key not set.")
            return {'CANCELLED'}
        if not endpoint_id:
            self.report({'ERROR'}, "Segment endpoint ID not set.")
            return {'CANCELLED'}

        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object first.")
            return {'CANCELLED'}

        # Export mesh as GLB
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

        payload = {"input": {"mesh": mesh_b64}}

        # Reset state
        cls = SEGMENT_OT_segment_mesh
        cls._thread = None
        cls._result = None
        cls._error = None
        cls._start_time = time.monotonic()

        wm = context.window_manager
        wm.segment_status = "Segmenting mesh..."

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
        cls = SEGMENT_OT_segment_mesh
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
            wm.segment_status = f"Error: {error[:80]}"
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        result = cls._result
        parts = result.get("parts", []) if result else []
        if not parts:
            wm.segment_status = "Error: no parts in response"
            self.report({'ERROR'}, "No parts in response")
            return {'CANCELLED'}

        # Create a collection for the parts
        collection = bpy.data.collections.new("Segmented Parts")
        context.scene.collection.children.link(collection)

        imported_count = 0
        for part in parts:
            part_b64 = part.get("mesh")
            part_name = part.get("name", f"part_{imported_count}")
            if not part_b64:
                continue

            tmp = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
            tmp.write(base64.b64decode(part_b64))
            tmp.close()
            try:
                existing = set(bpy.data.objects)
                bpy.ops.import_scene.gltf(filepath=tmp.name)
                new_objs = set(bpy.data.objects) - existing
                for obj in new_objs:
                    # Move to our collection
                    for col in obj.users_collection:
                        col.objects.unlink(obj)
                    collection.objects.link(obj)
                    obj.name = part_name
                imported_count += 1
            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)

        elapsed = time.monotonic() - cls._start_time
        wm.segment_status = f"Done ({imported_count} parts, {elapsed:.0f}s)"
        self.report({'INFO'}, f"Imported {imported_count} parts")
        return {'FINISHED'}

    def cancel(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None


def register():
    bpy.utils.register_class(SEGMENT_OT_segment_mesh)
    bpy.types.WindowManager.segment_status = StringProperty(
        name="Status", default="Idle",
    )


def unregister():
    del bpy.types.WindowManager.segment_status
    bpy.utils.unregister_class(SEGMENT_OT_segment_mesh)
