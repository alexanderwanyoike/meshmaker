## Card 1: Code Fixes and CI

Fix two known issues before testing, and enable container builds from dev so we can iterate without merging to main.

### Deliverables

**encoding.ts utility**
- Create `app/src/utils/encoding.ts` with chunked `uint8ArrayToBase64` (64KB chunks via `String.fromCharCode.apply`) and `base64ToUint8Array`
- Update `app/src/services/pipeline.ts` to import from `../utils/encoding` instead of defining locally

**RunPod timeout fix**
- Update `app/src/services/runpod.ts`: add optional `timeoutMs: number = 10 * 60 * 1000` param to `runJob` and `pollJob`
- Update error message to reflect actual timeout value
- In `app/src/services/pipeline.ts` `animateModel`: pass `30 * 60 * 1000` (30 min) for HyMotion cold starts

**CI: add dev branch triggers**
- `.github/workflows/build-push.yml` — add `dev` to push branches, add `paths: containers/hymotion/**` filter (currently missing, causes every commit to trigger expensive HyMotion build)
- `.github/workflows/build-trellis2.yml` — add `dev` to push branches
- `.github/workflows/build-unirig.yml` — add `dev` to push branches
- On dev builds, only SHA tag is applied (not `latest`) — this is already handled by `enable={{is_default_branch}}`

### Acceptance Criteria
- [ ] `cd app && yarn build` passes
- [ ] CI workflows trigger on push to `dev` and `main`
- [ ] `animateModel` passes 30-minute timeout to runJob

## Card 2: Suite UI

Expand the app from a single wizard into a 4-mode suite with a persistent sidebar. The full pipeline wizard is preserved as-is; three standalone tool views are added.

### Deliverables

**AppShell**
- Create `app/src/components/AppShell.tsx` — sidebar (180px) + content area
- Sidebar entries: Full Pipeline, Mesh Generator, Auto Rigger, Animator + Settings at bottom
- Mode state is local `useState<AppMode>` — no store changes
- Settings modal moves here (remove from Wizard)
- Update `app/src/App.tsx` to render `<AppShell />` instead of `<Wizard />`

**Wizard update**
- Add `hideHeader?: boolean` prop to `app/src/components/wizard/Wizard.tsx`
- When `hideHeader` is true, suppress the `<h1>CharMaker</h1>` and gear icon (they live in the sidebar now)
- Tauri window width: update `app/src-tauri/tauri.conf.json` from 800→960px

**useFilePicker additions**
- Add `pickGlb()` and `pickFbx()` to `app/src/hooks/useFilePicker.ts`

**Standalone tools** (each uses local `useState`, calls existing service functions directly)

`app/src/components/tools/MeshTool.tsx`
- Pick image → `generate3D(config, imagePath, onStatus)` → save dialog for GLB
- Shows status messages and errors inline
- "Save GLB" triggers `pickSaveLocation('model.glb')` then `writeFile`

`app/src/components/tools/RigTool.tsx`
- Pick GLB → read file bytes → `uint8ArrayToBase64` → create `GeneratedModel` shell → `rigModel(config, model, onStatus)` → save dialog for FBX
- Needs `readFile` from `@tauri-apps/plugin-fs` and `uint8ArrayToBase64` from `utils/encoding`

`app/src/components/tools/AnimateTool.tsx`
- Pick FBX + text prompt + duration slider → read file → `animateModel(config, riggedModel, prompt, duration, onStatus)` → save dialog for animated FBX
- Same file-reading pattern as RigTool but wraps bytes in a `RiggedModel` shell

### Acceptance Criteria
- [ ] `cd app && yarn build` passes with no TS errors
- [ ] All 4 modes render without crashing
- [ ] Settings accessible from sidebar in all modes
- [ ] Each standalone tool: pick file → run → save output

## Card 3: Test Scripts

Create Python test scripts for the two new containers, following the existing `scripts/test_unirig.py` pattern exactly.

### Deliverables

**`scripts/test_trellis.py`**
```
Usage: python scripts/test_trellis.py input.png output.glb [options]

Options:
  --resolution 512       Generation resolution (512/1024/1536)
  --texture-size 2048    Output texture size
  --seed N               Random seed
  --decimation N         Target face count
  --endpoint ID          RunPod endpoint ID (or TRELLIS_ENDPOINT_ID env)
  --api-key KEY          RunPod API key (or RUNPOD_API_KEY env)

Input payload:  { image: base64, resolution, texture_size, seed?, decimation_target? }
Output parsing: result["glb"] → save to output.glb
Stats printed:  total_time, generation_time, export_time, glb_size_bytes, seed
```

**`scripts/test_hymotion.py`**
```
Usage: python scripts/test_hymotion.py "prompt" output.fbx [options]

Options:
  --character-fbx PATH   Path to rigged FBX for retargeting (optional)
                         Without this flag: returns raw NPZ motion data
  --duration 4.0         Animation duration in seconds
  --fps 30               Frames per second
  --seed N               Random seed
  --guidance-scale 7.5   CFG scale
  --endpoint ID          RunPod endpoint ID (or HYMOTION_ENDPOINT_ID env)
  --api-key KEY          RunPod API key (or RUNPOD_API_KEY env)

Input payload:  { prompt, duration, fps, guidance_scale, seed?, character_fbx?: base64 }
Output:         With --character-fbx: result["animated_fbx"] → write .fbx
                Without:              result["motion_data"]   → write .npz
Stats printed:  generation_time, num_frames, seed, file size
```

Both scripts follow `test_unirig.py` exactly: argparse, env var credentials, `runsync` primary path with polling fallback, timing stats at the end.

### Acceptance Criteria
- [ ] `python scripts/test_trellis.py photo.png out.glb` produces a GLB file
- [ ] `python scripts/test_unirig.py out.glb rigged.fbx` produces an FBX
- [ ] `python scripts/test_hymotion.py "walk" anim.fbx --character-fbx rigged.fbx` produces an animated FBX
- [ ] `python scripts/test_hymotion.py "walk" motion.npz` (no FBX) produces an NPZ
