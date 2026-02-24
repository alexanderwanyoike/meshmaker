"""Blender operators for CharMaker."""

import base64
import os
import tempfile
import threading

import bpy
from bpy.props import EnumProperty, IntProperty, StringProperty
from bpy.types import Operator

from . import api

PREVIEW_NAME = "CharMaker Preview"


def _cleanup_preview():
    """Remove the preview image datablock and its temp file."""
    img = bpy.data.images.get(PREVIEW_NAME)
    if img is not None:
        path = bpy.path.abspath(img.filepath)
        bpy.data.images.remove(img)
        if path and os.path.isfile(path):
            os.unlink(path)


def _get_preview_b64():
    """Read the current preview image back as base64, or None."""
    img = bpy.data.images.get(PREVIEW_NAME)
    if img is None:
        return None
    path = bpy.path.abspath(img.filepath)
    if not path or not os.path.isfile(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


class CHARMAKER_OT_generate_image(Operator):
    bl_idname = "charmaker.generate_image"
    bl_label = "Generate Image"
    bl_description = "Generate or edit a concept image with Gemini"

    _thread = None
    _result = None
    _error = None
    _timer = None

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        api_key = prefs.gemini_api_key
        model = prefs.gemini_model

        if not api_key:
            self.report({'ERROR'}, "Gemini API key not set. Check addon preferences.")
            return {'CANCELLED'}

        wm = context.window_manager
        prompt = wm.charmaker_prompt.strip()
        if not prompt:
            self.report({'ERROR'}, "Enter a prompt first.")
            return {'CANCELLED'}

        # Check for existing preview (edit mode)
        image_b64 = _get_preview_b64()

        # Reset state
        cls = CHARMAKER_OT_generate_image
        cls._thread = None
        cls._result = None
        cls._error = None

        wm.charmaker_status = "Generating image..."

        def run():
            try:
                result = api.call_gemini(api_key, model, prompt, image_b64)
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
        cls = CHARMAKER_OT_generate_image
        thread = cls._thread

        if thread is not None and thread.is_alive():
            return {'PASS_THROUGH'}

        wm.event_timer_remove(self._timer)
        self._timer = None

        error = cls._error
        if error:
            wm.charmaker_status = f"Error: {error[:80]}"
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        image_bytes, text_response = cls._result

        # Clean up old preview
        _cleanup_preview()

        # Save new image to temp file
        try:
            tmp = tempfile.NamedTemporaryFile(
                suffix=".png", delete=False, prefix="charmaker_",
            )
            tmp.write(image_bytes)
            tmp.close()

            img = bpy.data.images.load(tmp.name)
            img.name = PREVIEW_NAME

            # Manually populate preview pixels — preview_ensure() is async
            # and won't be ready by the time the panel redraws.
            # Set both icon and image previews so template_icon works
            # at any scale.
            img.preview_ensure()
            w, h = img.size
            px = img.pixels[:]
            p = img.preview
            p.icon_size = (w, h)
            p.icon_pixels_float = px
            p.image_size = (w, h)
            p.image_pixels_float = px

            wm.charmaker_preview_image = PREVIEW_NAME

            wm.charmaker_status = "Image ready"
            if text_response:
                self.report({'INFO'}, text_response[:120])

        except Exception as e:
            wm.charmaker_status = f"Error: {str(e)[:60]}"
            self.report({'ERROR'}, f"Failed to load preview: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}

    def cancel(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None


class CHARMAKER_OT_clear_preview(Operator):
    bl_idname = "charmaker.clear_preview"
    bl_label = "Clear Preview"
    bl_description = "Discard the current preview image"

    def execute(self, context):
        _cleanup_preview()
        wm = context.window_manager
        wm.charmaker_preview_image = ""
        wm.charmaker_prompt = ""
        wm.charmaker_status = "Idle"
        return {'FINISHED'}


class CHARMAKER_OT_generate_mesh(Operator):
    bl_idname = "charmaker.generate_mesh"
    bl_label = "Generate 3D Mesh"
    bl_description = "Generate a 3D mesh from an image using Trellis 2"

    image_path: StringProperty(
        name="Image",
        description="Path to the reference image",
        subtype='FILE_PATH',
    )

    resolution: EnumProperty(
        name="Resolution",
        items=[
            ('512', "512", "Fast, lower quality"),
            ('1024', "1024", "Balanced"),
            ('1536', "1536", "Slow, higher quality"),
        ],
        default='512',
    )

    texture_size: EnumProperty(
        name="Texture Size",
        items=[
            ('1024', "1024", "Smaller file size"),
            ('2048', "2048", "Balanced (default)"),
            ('4096', "4096", "High quality textures"),
        ],
        default='2048',
    )

    seed: IntProperty(
        name="Seed",
        description="Random seed (0 = random)",
        default=0,
        min=0,
    )

    # Internal state (not shown in UI)
    _thread = None
    _result = None
    _error = None
    _timer = None

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        api_key = prefs.runpod_api_key
        endpoint_id = prefs.trellis_endpoint_id

        if not api_key:
            self.report({'ERROR'}, "RunPod API key not set. Check addon preferences.")
            return {'CANCELLED'}
        if not endpoint_id:
            self.report({'ERROR'}, "Trellis endpoint ID not set. Check addon preferences.")
            return {'CANCELLED'}

        # Resolve image path — fall back to preview if no explicit path
        image_path = bpy.path.abspath(self.image_path) if self.image_path else ""
        if not image_path or not os.path.isfile(image_path):
            preview = bpy.data.images.get(PREVIEW_NAME)
            if preview is not None:
                image_path = bpy.path.abspath(preview.filepath)

        if not image_path or not os.path.isfile(image_path):
            self.report({'ERROR'}, "No image available. Generate or select one first.")
            return {'CANCELLED'}

        # Read and encode the image
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        payload_input = {
            "image": image_b64,
            "resolution": int(self.resolution),
            "texture_size": int(self.texture_size),
        }
        if self.seed > 0:
            payload_input["seed"] = self.seed

        payload = {"input": payload_input}

        # Reset state
        CHARMAKER_OT_generate_mesh._thread = None
        CHARMAKER_OT_generate_mesh._result = None
        CHARMAKER_OT_generate_mesh._error = None

        # Update status
        wm = context.window_manager
        wm.charmaker_status = "Generating mesh..."

        # Launch background thread
        def run():
            try:
                result = api.call_runpod(api_key, endpoint_id, payload)
                CHARMAKER_OT_generate_mesh._result = result
            except Exception as e:
                CHARMAKER_OT_generate_mesh._error = str(e)

        CHARMAKER_OT_generate_mesh._thread = threading.Thread(target=run, daemon=True)
        CHARMAKER_OT_generate_mesh._thread.start()

        # Start modal timer
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        wm = context.window_manager
        thread = CHARMAKER_OT_generate_mesh._thread

        # Still running
        if thread is not None and thread.is_alive():
            return {'PASS_THROUGH'}

        # Done — clean up timer
        wm.event_timer_remove(self._timer)
        self._timer = None

        # Check for errors
        error = CHARMAKER_OT_generate_mesh._error
        if error:
            wm.charmaker_status = f"Error: {error[:80]}"
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        # Extract GLB
        result = CHARMAKER_OT_generate_mesh._result
        glb_b64 = result.get("glb") if result else None
        if not glb_b64:
            wm.charmaker_status = "Error: no GLB in response"
            self.report({'ERROR'}, "No GLB data in response")
            return {'CANCELLED'}

        # Write temp file and import
        tmp = None
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
            tmp.write(base64.b64decode(glb_b64))
            tmp.close()

            bpy.ops.import_scene.gltf(filepath=tmp.name)

            meta = result.get("metadata", {})
            seed_str = meta.get("seed", "n/a")
            gen_time = meta.get("generation_time", "?")
            wm.charmaker_status = f"Done (seed={seed_str}, {gen_time}s)"
            self.report({'INFO'}, f"Mesh imported (seed={seed_str})")

        except Exception as e:
            wm.charmaker_status = f"Import error: {str(e)[:60]}"
            self.report({'ERROR'}, f"Failed to import GLB: {e}")
            return {'CANCELLED'}
        finally:
            if tmp and os.path.exists(tmp.name):
                os.unlink(tmp.name)

        return {'FINISHED'}

    def cancel(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None


def register():
    bpy.utils.register_class(CHARMAKER_OT_generate_image)
    bpy.utils.register_class(CHARMAKER_OT_clear_preview)
    bpy.utils.register_class(CHARMAKER_OT_generate_mesh)

    wm = bpy.types.WindowManager
    wm.charmaker_status = StringProperty(name="Status", default="Idle")
    wm.charmaker_prompt = StringProperty(
        name="Prompt",
        description="Text prompt for Gemini image generation",
    )
    wm.charmaker_preview_image = StringProperty(
        name="Preview Image",
        description="Name of the preview image datablock",
    )


def unregister():
    # Clean up any remaining preview
    _cleanup_preview()

    wm = bpy.types.WindowManager
    del wm.charmaker_preview_image
    del wm.charmaker_prompt
    del wm.charmaker_status

    bpy.utils.unregister_class(CHARMAKER_OT_generate_mesh)
    bpy.utils.unregister_class(CHARMAKER_OT_clear_preview)
    bpy.utils.unregister_class(CHARMAKER_OT_generate_image)
