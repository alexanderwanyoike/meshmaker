# CharMaker

End-to-end AI pipeline for creating animated game characters from text or images.

```
Text/Image → 3D Model → Rigged Character → Animated Character → Game-Ready
    ↓            ↓              ↓                  ↓                 ↓
 Prompt     Trellis 2       UniRig           HY-Motion           FBX/GLB
            Hunyuan 3D       (GLB→FBX)        (text→motion)
```

## Project Status

**Active development.** Currently restructuring from a single-purpose motion generator into a full character pipeline.

See `.notes/` for detailed planning documents:
- `charmaker-vision.md` - Full vision and architecture
- `card-*.md` - Implementation cards for each phase

## Repository Structure

```
charmaker/
├── app/                    # Tauri desktop app (planned)
├── containers/
│   └── hymotion/           # Text-to-animation container (working)
│       ├── Dockerfile
│       ├── handler.py
│       └── stats/
├── shared/                 # Shared utilities (planned)
└── .notes/                 # Planning documents
```

## Current Capability: HY-Motion Container

The `containers/hymotion/` directory contains a working RunPod serverless container for text-to-animation generation using [HY-Motion-1.0](https://github.com/Tencent-Hunyuan/HY-Motion-1.0).

### Quick Start

1. Push to GitHub - image builds via GitHub Actions to `ghcr.io/<user>/charmaker/hymotion:latest`
2. Make the package public in GitHub Package settings
3. Create RunPod endpoint with 48GB GPU and network volume mounted at `/runpod-volume`
4. Send requests with text prompts, receive SMPL-H motion data

### API

```bash
curl -X POST "https://api.runpod.ai/v2/${ENDPOINT_ID}/run" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "person walking forward",
      "duration": 4.0,
      "fps": 30
    }
  }'
```

## Roadmap

| Card | Component | Status |
|------|-----------|--------|
| 0 | Repo restructure | In Progress |
| 1 | Trellis 2 / Hunyuan 3D container | Planned |
| 2 | UniRig container | Planned |
| 3 | HY-Motion update (retargeting) | Planned |
| 4 | Tauri app scaffold | Planned |
| 5 | Pipeline integration | Planned |
| 6 | Testing & docs | Planned |

## Links

- [HY-Motion-1.0](https://github.com/Tencent-Hunyuan/HY-Motion-1.0) - Text-to-motion model
- [Trellis 2](https://github.com/microsoft/TRELLIS.2) - Image/text to 3D (planned)
- [UniRig](https://github.com/VAST-AI-Research/UniRig) - Auto-rigging (planned)
- [RunPod Serverless](https://docs.runpod.io/serverless) - GPU infrastructure
