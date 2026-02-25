"""Blender operators for AnimMaker."""

import threading
import time

import bpy
from bpy.props import FloatProperty, IntProperty, StringProperty
from bpy.types import Operator

from . import api, retarget


class ANIMMAKER_OT_animate(Operator):
    bl_idname = "animmaker.animate"
    bl_label = "Animate"
    bl_description = "Generate animation from text prompt via HY-Motion"

    _thread = None
    _result = None
    _error = None
    _timer = None
    _start_time = None
    _armature_name = None

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        api_key = prefs.runpod_api_key
        endpoint_id = prefs.hymotion_endpoint_id

        if not api_key:
            self.report({'ERROR'}, "RunPod API key not set. Check addon preferences.")
            return {'CANCELLED'}
        if not endpoint_id:
            self.report({'ERROR'}, "HY-Motion endpoint ID not set. Check addon preferences.")
            return {'CANCELLED'}

        obj = context.active_object
        if obj is None or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature first.")
            return {'CANCELLED'}

        if "bone_0" not in obj.data.bones:
            self.report({'ERROR'}, "Selected armature is not a UniRig armature (no bone_0).")
            return {'CANCELLED'}

        wm = context.window_manager
        prompt = wm.animmaker_prompt.strip()
        if not prompt:
            self.report({'ERROR'}, "Enter an animation prompt.")
            return {'CANCELLED'}

        duration = wm.animmaker_duration
        fps = wm.animmaker_fps
        seed = wm.animmaker_seed
        guidance = wm.animmaker_guidance

        payload_input = {
            "prompt": prompt,
            "duration": duration,
            "fps": fps,
            "guidance_scale": guidance,
        }
        if seed > 0:
            payload_input["seed"] = seed
        payload = {"input": payload_input}

        # Reset state
        cls = ANIMMAKER_OT_animate
        cls._thread = None
        cls._result = None
        cls._error = None
        cls._start_time = time.monotonic()
        cls._armature_name = obj.name

        wm.animmaker_status = "Generating animation..."

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
        cls = ANIMMAKER_OT_animate
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
            wm.animmaker_status = f"Error: {error[:80]}"
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        result = cls._result
        if not result:
            wm.animmaker_status = "Error: empty response"
            self.report({'ERROR'}, "Empty response from HY-Motion")
            return {'CANCELLED'}

        # Look up armature by name
        armature = bpy.data.objects.get(cls._armature_name)
        if armature is None:
            wm.animmaker_status = "Error: armature deleted"
            self.report({'ERROR'}, "Armature was deleted during processing")
            return {'CANCELLED'}

        # Apply motion
        try:
            num_frames = retarget.apply_motion(armature, result)
        except Exception as e:
            wm.animmaker_status = f"Error: {str(e)[:60]}"
            self.report({'ERROR'}, f"Failed to apply motion: {e}")
            return {'CANCELLED'}

        elapsed = time.monotonic() - cls._start_time
        seed_val = result.get("metadata", {}).get("seed", "n/a")
        wm.animmaker_status = f"Done ({num_frames} frames, {elapsed:.0f}s, seed={seed_val})"
        self.report({'INFO'}, f"Animation applied: {num_frames} frames")

        return {'FINISHED'}

    def cancel(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None


def register():
    bpy.utils.register_class(ANIMMAKER_OT_animate)

    wm = bpy.types.WindowManager
    wm.animmaker_status = StringProperty(name="Status", default="Idle")
    wm.animmaker_prompt = StringProperty(
        name="Prompt",
        description="Text description of the animation",
    )
    wm.animmaker_duration = FloatProperty(
        name="Duration",
        description="Animation duration in seconds",
        default=4.0,
        min=0.5,
        max=12.0,
    )
    wm.animmaker_fps = IntProperty(
        name="FPS",
        description="Frames per second",
        default=30,
        min=15,
        max=60,
    )
    wm.animmaker_seed = IntProperty(
        name="Seed",
        description="Random seed (0 = random)",
        default=0,
        min=0,
    )
    wm.animmaker_guidance = FloatProperty(
        name="Guidance Scale",
        description="Classifier-free guidance scale",
        default=7.5,
        min=1.0,
        max=20.0,
    )


def unregister():
    wm = bpy.types.WindowManager
    del wm.animmaker_guidance
    del wm.animmaker_seed
    del wm.animmaker_fps
    del wm.animmaker_duration
    del wm.animmaker_prompt
    del wm.animmaker_status

    bpy.utils.unregister_class(ANIMMAKER_OT_animate)
