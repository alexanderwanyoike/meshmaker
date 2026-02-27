"""
Minimal Gradio mock so MIA's app.py can be imported without a real Gradio
installation or Gradio server. Only stubs the parts used in the inference
pipeline — UI components are no-ops.
"""
import sys
import types


def _make_mock():
    gr = types.ModuleType("gradio")

    # State component — used as dict key in stage function returns
    class State:
        def __init__(self, *args, **kwargs):
            pass

    gr.State = State
    gr.Success = lambda msg="": print(f"[MIA] {msg}")
    gr.Info = lambda msg="": print(f"[MIA] {msg}")
    gr.Warning = lambda msg="": print(f"[MIA WARNING] {msg}")

    def _error(msg=""):
        raise RuntimeError(msg)

    gr.Error = _error

    # GPU decorator (HuggingFace Spaces) — identity
    def _gpu(fn=None, **kwargs):
        if fn is not None:
            return fn
        return lambda f: f

    gr.GPU = _gpu

    # Stub UI components as no-op classes
    def _stub(name):
        return type(name, (), {"__init__": lambda self, *a, **k: None})

    for name in [
        "Blocks", "Row", "Column", "Tab", "Tabs", "Accordion",
        "Image", "Model3D", "File", "Textbox", "Slider", "Checkbox",
        "Button", "Dropdown", "Radio", "Number", "Markdown", "HTML",
        "Gallery", "Video", "Audio", "Label", "HighlightedText",
        "Dataframe", "Plot", "JSON", "Code", "update", "Request",
    ]:
        setattr(gr, name, _stub(name))

    # Stub submodules
    for sub in ["components", "themes", "helpers", "routes", "utils"]:
        mod = types.ModuleType(f"gradio.{sub}")
        sys.modules[f"gradio.{sub}"] = mod
        setattr(gr, sub, mod)

    return gr


def install():
    """Insert mock into sys.modules before any MIA code imports gradio."""
    if "gradio" not in sys.modules:
        sys.modules["gradio"] = _make_mock()
