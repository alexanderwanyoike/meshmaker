# CharMaker

End-to-end AI pipeline for creating animated game characters from text or images.

```
Text/Image → 3D Model → Rigged Character → Animated Character → Game-Ready
    ↓            ↓              ↓                  ↓                 ↓
 Prompt     Trellis 2       UniRig           HY-Motion           FBX/GLB
            Hunyuan 3D       (GLB→FBX)        (text→motion)
```

## Project Status

**Active development.** The frontend is a Blender addon — Blender provides the viewport, mesh editing, rigging, and animation tools.

See `.notes/` for detailed planning documents:
- `charmaker-vision.md` - Full vision and architecture
- `card-*.md` - Implementation cards for each phase

## Repository Structure

```
charmaker/
├── addon/                  # Blender addon (CharMaker panel)
├── containers/
│   ├── hymotion/           # Text-to-animation container (working)
│   │   ├── Dockerfile
│   │   ├── handler.py
│   │   └── stats/
│   └── trellis2/           # Image-to-3D container (working)
│       ├── Dockerfile
│       └── handler.py
├── scripts/                # CLI test scripts
└── .notes/                 # Planning documents
```

## Blender Addon

The `addon/` directory is a Blender addon that calls RunPod serverless endpoints to generate 3D meshes directly into Blender.

### Install

1. Edit → Preferences → Add-ons → Install from Disk
2. Select the `addon/` folder
3. Enable "CharMaker" in the addon list
4. Set your RunPod API key and Trellis endpoint ID in addon preferences

### Usage

1. Open the sidebar (N key) → CharMaker tab
2. Pick a reference image
3. Adjust resolution / texture size
4. Click "Generate 3D"

## Roadmap

| Card | Component | Status |
|------|-----------|--------|
| 0 | Repo restructure | Done |
| 1 | Trellis 2 container | Done |
| 2 | UniRig container | Planned |
| 3 | HY-Motion update (retargeting) | Planned |
| 5 | Pipeline integration | Planned |
| 6 | Testing & docs | Planned |

## Links

- [HY-Motion-1.0](https://github.com/Tencent-Hunyuan/HY-Motion-1.0) - Text-to-motion model
- [Trellis 2](https://github.com/microsoft/TRELLIS.2) - Image/text to 3D
- [UniRig](https://github.com/VAST-AI-Research/UniRig) - Auto-rigging (planned)
- [RunPod Serverless](https://docs.runpod.io/serverless) - GPU infrastructure
