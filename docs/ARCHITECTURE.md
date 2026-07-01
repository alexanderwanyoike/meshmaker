# MeshMaker - Architecture

> The "how" behind `VISION.md`. Read VISION first for the what/why.

## The one organizing idea: the provider spine

MeshMaker does exactly one thing - image-to-3D - and organizes its code around a single small abstraction: the **provider**.

- A **provider** is a concrete hosted backend that turns an image into a mesh: `FalHunyuan3DProvider`, `MeshyProvider`, and whatever comes next.
- Every provider implements one method, `generate`, and declares which addon preference holds its API key.
- The Blender UI never knows which provider it is talking to. It builds a typed `GenerateRequest`, the registry hands it a provider, and it gets back an `Asset`.

This is what keeps MeshMaker from becoming a pile of scripts. A new idea is either a new **provider** or a **UI change**. Nothing floats.

## The provider interface

```python
@dataclass(frozen=True)
class Asset:
    url: str                 # hosted GLB to download and import
    format: str = "glb"
    name: str | None = None
    metadata: dict = ...

@dataclass(frozen=True)
class GenerateRequest:
    api_key: str
    image: bytes             # raw reference image; providers encode a data URI
    face_count: int = 50000
    enable_pbr: bool = False

class Provider:
    id: str
    name: str
    api_key_pref_field: str  # which addon preference holds this provider's key

    def generate(self, req: GenerateRequest) -> Asset: ...
```

`Asset` is always a hosted URL, never raw base64. Both Fal and Meshy accept the
reference image as an inline base64 data URI, so there is no separate upload step.

## Repo layout

```
meshmaker/                     # Blender addon (the client)
  __init__.py                  # entry point, panel/operator registration
  api.py                       # HTTP helpers + Gemini client (stdlib only)
  preferences.py               # Fal / Meshy / Gemini API keys
  mesh/                        # the MeshMaker tab
    operators.py               #   Gemini image-gen + generate-mesh operators
    panels.py                  #   the sidebar UI
  providers/                   # the provider spine
    base.py                    #   Provider, GenerateRequest, Asset
    common.py                  #   ProviderError, data_uri, poll policy
    fal/                       #   queue transport + Hunyuan3D/Pixal3D/Tripo/Rodin
    meshy.py                   #   MeshyProvider
    registry.py                #   the active provider list
docs/                          # vision, architecture, reference, cards
tests/                         # provider mapping + HTTP helper tests
```

## Data flow

```
Blender (MeshMaker tab)
  -> (optional) prompt -> api.call_gemini -> concept image
  -> build GenerateRequest{ api_key, image, face_count, enable_pbr }
  -> registry.resolve(provider_id).generate(req)
       Fal:   POST queue.fal.run/{model} -> poll status_url -> GET response_url
       Meshy: POST api.meshy.ai/.../image-to-3d -> poll task -> read model_urls.glb
  -> Asset{ url, metadata }            # always a hosted URL
  -> api.download(url) -> temp .glb -> bpy.ops.import_scene.gltf
```

The provider call and the GLB download both run on a worker thread; only the
Blender import (`bpy.ops`) runs on the main thread via the operator's modal loop.

## The transport rule

**Providers return asset URLs, never inline bytes.** The client downloads the
URL and imports it. This sidesteps the response-size ceilings that forced quality
compromises in the old self-hosted path, and it means a provider's only job is to
map its API response to a single `Asset.url`.

## Adding a provider

1. Add a `StringProperty` for the API key in `preferences.py` (Fal models reuse
   the existing `fal_api_key`).
2. Subclass `Provider` in its own module - a Fal model is a `FalQueueProvider`
   subclass in `providers/fal/`; anything else gets its own module. Implement
   `generate` (or just `_payload` for a Fal model) and set `api_key_pref_field`.
3. Add the instance to `_PROVIDERS` in `registry.py`.

The provider dropdown, key check, and import path all pick it up automatically.
Add a unit test (`tests/test_fal.py` for a Fal model, else a new `tests/test_*.py`)
that mocks the HTTP layer and asserts the request shape and the
response-to-`Asset` mapping.

## What is deliberately not here

Rigging, animation, and segmentation are separate tools, not capabilities of
MeshMaker. There is no `Capability` enum, no RunPod transport, and no container
build pipeline. If those tools are ever built, the old handlers live in git
history on `dev`.
