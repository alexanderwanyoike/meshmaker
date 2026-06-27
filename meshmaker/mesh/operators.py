"""Blender operators for MeshMaker mesh generation."""

import base64
import os
import tempfile
import threading

import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty
from bpy.types import Operator

from .. import ADDON_ID, api
from ..providers import registry
from ..providers.base import GenerateRequest

PREVIEW_NAME = "MeshMaker Preview"

# ---------------------------------------------------------------------------
# Model registry - derived from the registered Generate providers.
# ---------------------------------------------------------------------------
_GENERATE_PROVIDERS = registry.list_providers()
MESH_MODELS = {
    provider.id: {
        "label": provider.name,
        "description": provider.description,
        "api_key_field": provider.api_key_pref_field,
    }
    for provider in _GENERATE_PROVIDERS
}

# Blender EnumProperty items built from the registry
MESH_MODEL_ITEMS = [
    (key, info["label"], info["description"])
    for key, info in MESH_MODELS.items()
]
_DEFAULT_MODEL = MESH_MODEL_ITEMS[0][0] if MESH_MODEL_ITEMS else ""


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


class MESHMAKER_OT_generate_image(Operator):
    bl_idname = "meshmaker.generate_image"
    bl_label = "Generate Image"
    bl_description = "Generate or edit a concept image with Gemini"

    _thread = None
    _result = None
    _error = None
    _timer = None

    def execute(self, context):
        prefs = context.preferences.addons[ADDON_ID].preferences
        api_key = prefs.gemini_api_key
        model = prefs.gemini_model

        if not api_key:
            self.report({'ERROR'}, "Gemini API key not set. Check addon preferences.")
            return {'CANCELLED'}

        wm = context.window_manager
        prompt = wm.meshmaker_prompt.strip()
        if not prompt:
            self.report({'ERROR'}, "Enter a prompt first.")
            return {'CANCELLED'}

        # Check for existing preview (edit mode)
        image_b64 = _get_preview_b64()

        # Reset state
        cls = MESHMAKER_OT_generate_image
        cls._thread = None
        cls._result = None
        cls._error = None

        wm.meshmaker_status = "Generating image..."

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
        cls = MESHMAKER_OT_generate_image
        thread = cls._thread

        if thread is not None and thread.is_alive():
            return {'PASS_THROUGH'}

        wm.event_timer_remove(self._timer)
        self._timer = None

        error = cls._error
        if error:
            wm.meshmaker_status = f"Error: {error[:80]}"
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        image_bytes, text_response = cls._result

        # Clean up old preview
        _cleanup_preview()

        # Save new image to temp file
        try:
            tmp = tempfile.NamedTemporaryFile(
                suffix=".png", delete=False, prefix="meshmaker_",
            )
            tmp.write(image_bytes)
            tmp.close()

            img = bpy.data.images.load(tmp.name)
            img.name = PREVIEW_NAME

            img.preview_ensure()
            w, h = img.size
            px = img.pixels[:]
            p = img.preview
            p.icon_size = (w, h)
            p.icon_pixels_float = px
            p.image_size = (w, h)
            p.image_pixels_float = px

            wm.meshmaker_preview_image = PREVIEW_NAME

            wm.meshmaker_status = "Image ready"
            if text_response:
                self.report({'INFO'}, text_response[:120])

        except Exception as e:
            wm.meshmaker_status = f"Error: {str(e)[:60]}"
            self.report({'ERROR'}, f"Failed to load preview: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}

    def cancel(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None


class MESHMAKER_OT_clear_preview(Operator):
    bl_idname = "meshmaker.clear_preview"
    bl_label = "Clear Preview"
    bl_description = "Discard the current preview image"

    def execute(self, context):
        _cleanup_preview()
        wm = context.window_manager
        wm.meshmaker_preview_image = ""
        wm.meshmaker_prompt = ""
        wm.meshmaker_status = "Idle"
        return {'FINISHED'}


class MESHMAKER_OT_generate_mesh(Operator):
    bl_idname = "meshmaker.generate_mesh"
    bl_label = "Generate 3D Mesh"
    bl_description = "Generate a 3D mesh from an image using the selected provider"

    image_path: StringProperty(
        name="Image",
        description="Path to the reference image",
        subtype='FILE_PATH',
    )

    face_count: IntProperty(
        name="Face Count",
        description="Target polygon count for the generated mesh",
        default=50000,
        min=40000,
        max=500000,
    )

    enable_pbr: BoolProperty(
        name="PBR Materials",
        description="Request PBR material maps (may cost extra)",
        default=False,
    )

    # Internal state (not shown in UI)
    _thread = None
    _result = None
    _error = None
    _timer = None

    def execute(self, context):
        prefs = context.preferences.addons[ADDON_ID].preferences

        wm = context.window_manager
        model_key = wm.meshmaker_model_backend
        model = MESH_MODELS[model_key]
        provider = registry.resolve(model_key)
        api_key = getattr(prefs, model["api_key_field"], "")

        if not api_key:
            self.report({'ERROR'}, f"{model['label']} API key not set. Check addon preferences.")
            return {'CANCELLED'}

        # Resolve image path - fall back to preview if no explicit path
        image_path = bpy.path.abspath(self.image_path) if self.image_path else ""
        if not image_path or not os.path.isfile(image_path):
            preview = bpy.data.images.get(PREVIEW_NAME)
            if preview is not None:
                image_path = bpy.path.abspath(preview.filepath)

        if not image_path or not os.path.isfile(image_path):
            self.report({'ERROR'}, "No image available. Generate or select one first.")
            return {'CANCELLED'}

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        request = GenerateRequest(
            api_key=api_key,
            image=image_bytes,
            face_count=self.face_count,
            enable_pbr=self.enable_pbr,
        )

        # Reset state
        cls = MESHMAKER_OT_generate_mesh
        cls._thread = None
        cls._result = None
        cls._error = None

        wm.meshmaker_status = f"Generating mesh ({model['label']})..."

        def run():
            try:
                asset = provider.generate(request)
                glb_bytes = api.download(asset.url)
                cls._result = (asset, glb_bytes)
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
        cls = MESHMAKER_OT_generate_mesh
        thread = cls._thread

        if thread is not None and thread.is_alive():
            return {'PASS_THROUGH'}

        wm.event_timer_remove(self._timer)
        self._timer = None

        error = cls._error
        if error:
            wm.meshmaker_status = f"Error: {error[:80]}"
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        result = cls._result
        if result is None:
            wm.meshmaker_status = "Error: no model in response"
            self.report({'ERROR'}, "No model in response")
            return {'CANCELLED'}

        asset, glb_bytes = result

        tmp = None
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
            tmp.write(glb_bytes)
            tmp.close()

            bpy.ops.import_scene.gltf(filepath=tmp.name)

            seed_str = asset.metadata.get("seed", "n/a")
            wm.meshmaker_status = f"Done (seed={seed_str})"
            self.report({'INFO'}, f"Mesh imported (seed={seed_str})")

        except Exception as e:
            wm.meshmaker_status = f"Import error: {str(e)[:60]}"
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
    bpy.utils.register_class(MESHMAKER_OT_generate_image)
    bpy.utils.register_class(MESHMAKER_OT_clear_preview)
    bpy.utils.register_class(MESHMAKER_OT_generate_mesh)

    wm = bpy.types.WindowManager
    wm.meshmaker_status = StringProperty(name="Status", default="Idle")
    wm.meshmaker_prompt = StringProperty(
        name="Prompt",
        description="Text prompt for Gemini image generation",
    )
    wm.meshmaker_preview_image = StringProperty(
        name="Preview Image",
        description="Name of the preview image datablock",
    )
    wm.meshmaker_model_backend = EnumProperty(
        name="Provider",
        items=MESH_MODEL_ITEMS,
        default=_DEFAULT_MODEL,
    )


def unregister():
    _cleanup_preview()

    wm = bpy.types.WindowManager
    del wm.meshmaker_model_backend
    del wm.meshmaker_preview_image
    del wm.meshmaker_prompt
    del wm.meshmaker_status

    bpy.utils.unregister_class(MESHMAKER_OT_generate_mesh)
    bpy.utils.unregister_class(MESHMAKER_OT_clear_preview)
    bpy.utils.unregister_class(MESHMAKER_OT_generate_image)
