# MeshMaker

Open-source Blender addon that generates 3D meshes from images using hosted AI
providers. Type a prompt (or pick an image), and a textured mesh lands in your
scene. Bring your own API keys; nothing runs on your GPU.

```
Prompt ──→ Gemini image ──→ 3D mesh
                             ▲
Image file ──────────────────┘
```

MeshMaker is **Generate-only by design**. Rigging, animation, and segmentation
are handled by separate, focused tools.

## Providers

| Provider | Model | Endpoint | Key |
|----------|-------|----------|-----|
| **Fal** | Hunyuan3D 3.1 | `fal-ai/hunyuan-3d/v3.1/{tier}/image-to-3d` | Fal API key |
| **Fal** | Pixal3D | `fal-ai/pixal3d` | Fal API key |
| **Fal** | Tripo v2.5 | `tripo3d/tripo/v2.5/image-to-3d` | Fal API key |
| **Fal** | Hyper3D Rodin | `fal-ai/hyper3d/rodin` | Fal API key |
| **Meshy** | Image to 3D (textured) | `api.meshy.ai/openapi/v1/image-to-3d` | Meshy API key |

All return a hosted GLB URL, which the addon downloads and imports. The four
Fal-hosted models share one **Fal API key**. Adding another Fal model is a tiny
`_FalQueueProvider` subclass in `meshmaker/providers/cloud.py` plus one line in
`registry.py`; the queue submit/poll transport is shared.

## Repo structure

```
meshmaker/                    # Blender addon (install as zip)
├── __init__.py               # entry point, panel/operator registration
├── api.py                    # HTTP helpers + Gemini client (stdlib only)
├── preferences.py            # Fal / Meshy / Gemini API keys
├── mesh/                     # the MeshMaker tab (image/prompt → 3D)
└── providers/                # the provider spine
    ├── base.py               #   Provider, GenerateRequest, Asset
    ├── cloud.py              #   Fal (Hunyuan3D, Pixal3D, Tripo, Rodin) + Meshy
    └── registry.py           #   the list of active providers
docs/                         # vision, architecture, reference, cards
tests/                        # provider mapping + HTTP helper tests
```

## Install

1. Download `meshmaker.zip` from [Releases](../../releases), or build it:
   ```
   make meshmaker
   ```
2. In Blender: **Edit > Preferences > Add-ons > Install from Disk** > select `meshmaker.zip`
3. Enable **MeshMaker** in the addon list
4. In addon preferences, set the keys you need:
   - **Fal API Key** and/or **Meshy API Key** (the Generate providers)
   - **Gemini API Key** (for the prompt → image step)

## Usage

Open the sidebar (**N** key) and find the **MeshMaker** tab:

1. Pick a **Provider** (Hunyuan3D, Pixal3D, Tripo or Rodin on Fal, or Meshy).
2. Either type a prompt to generate a concept image with Gemini, or switch to
   **Use File** and point at an image.
3. Set **Face Count** and **PBR Materials**, then **Generate 3D**. The mesh
   downloads from the provider's hosted URL and imports into your scene.

## Adding a provider

```python
# meshmaker/providers/cloud.py
class MyProvider(Provider):
    id = "MY_PROVIDER"
    name = "My Provider"
    api_key_pref_field = "my_api_key"   # add the StringProperty in preferences.py

    def generate(self, req: GenerateRequest) -> Asset:
        ...
        return Asset(url=hosted_glb_url, format="glb")
```

Register the instance in `meshmaker/providers/registry.py` and it appears in the
provider dropdown automatically.

## License

MIT - see [LICENSE](LICENSE). The hosted models (Hunyuan3D, Pixal3D, Tripo,
Rodin, Meshy) are governed by their providers' terms.
