# MeshMaker

Open-source AI character pipeline for Blender. Generate 3D meshes from images or text, auto-rig them, animate them, and segment them into parts — all from the Blender sidebar. AI models run on [RunPod](https://www.runpod.io/) serverless GPUs.

```
Image/Text ──→ 3D Mesh ──→ Rigged Character ──→ Animated Character
                  │
                  └──→ Part Segmentation
```

## Models

| Model | Task | Container | GPU | License |
|-------|------|-----------|-----|---------|
| [Trellis 2](https://github.com/microsoft/TRELLIS.2) (4B) | Image → 3D mesh | `containers/trellis2/` | 48GB+ (A100/H100) | MIT |
| [Hunyuan3D 2.1](https://github.com/Tencent/Hunyuan3D-2) | Image/text → 3D mesh | `containers/hunyuan3d/` | 48GB+ (A6000/A100/H100) | Tencent |
| [MIA](https://github.com/jasongzy/Make-It-Animatable) | Mesh → rigged FBX | `containers/mia/` | 24GB+ | Apache 2.0 |
| [HY-Motion 1.0](https://github.com/Tencent-Hunyuan/HY-Motion-1.0) | Text → animation | `containers/hymotion/` | 24GB+ | Tencent |
| [Hunyuan3D-Part](https://github.com/Tencent/Hunyuan3D-2) (P3-SAM) | Mesh → part segments | `containers/hunyuan3d-part/` | 24GB+ | Tencent |

## Repo Structure

```
meshmaker/                    # Blender addon (install as zip)
├── __init__.py               # Unified entry point
├── api.py                    # Shared RunPod + Gemini API client
├── preferences.py            # All endpoint IDs + API keys
├── mesh/                     # MeshMaker tab (image/text → 3D)
├── rig/                      # RigMaker tab (mesh → rigged)
├── anim/                     # AnimMaker tab (rig → animated)
└── segment/                  # PartMaker tab (mesh → parts)
containers/
├── trellis2/                 # Trellis 2 RunPod container
├── hunyuan3d/                # Hunyuan3D 2.1 RunPod container
├── mia/                      # Make It Animatable RunPod container
├── hymotion/                 # HY-Motion RunPod container
└── hunyuan3d-part/           # P3-SAM part segmentation container
scripts/                      # CLI test scripts
```

## Install

1. Download `meshmaker.zip` from [Releases](../../releases), or build it yourself:
   ```
   make meshmaker
   ```
2. In Blender: **Edit → Preferences → Add-ons → Install from Disk** → select `meshmaker.zip`
3. Enable **MeshMaker** in the addon list
4. In addon preferences, configure:
   - **RunPod API Key**
   - **Endpoint IDs** for each model you want to use
   - **Gemini API Key** (optional — for AI image generation)

## Usage

Open the sidebar (**N** key) to find four tabs:

| Tab | What it does |
|-----|-------------|
| **MeshMaker** | Generate 3D meshes from images or text. Supports Trellis 2 and Hunyuan3D 2.1 backends. |
| **RigMaker** | Auto-rig a mesh with a Mixamo skeleton via MIA. |
| **AnimMaker** | Animate a rigged character from a text prompt via HY-Motion. |
| **PartMaker** | Segment a mesh into semantic parts via P3-SAM. |

## Deploy Containers

Each container has a CI workflow that builds and pushes to GHCR on push to `main` or `dev`. You can also build locally:

```
make trellis2        # or hunyuan3d, hunyuan3d-part, mia
```

To deploy on RunPod:

1. Create a **Serverless Endpoint** in the RunPod console
2. Set the container image to the GHCR URL (e.g. `ghcr.io/<owner>/trellis2:<tag>`)
3. Select GPU tier per the table above
4. Copy the endpoint ID into MeshMaker addon preferences

## License

MIT — see [LICENSE](LICENSE). Individual AI models have their own licenses (see [Models](#models) table).
