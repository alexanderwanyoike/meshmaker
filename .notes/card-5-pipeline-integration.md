# Card 5: Pipeline Integration

**Status:** Not Started
**Size:** Large (~3-5 days)
**Dependencies:** Cards 1, 2, 3, 4

---

## Goal

Connect Tauri app to RunPod containers.

---

## Deliverables

- RunPod API client (TypeScript or Rust)
- Environment config for API keys
- Pipeline orchestration:
  1. Upload image → Trellis 2 → GLB
  2. Send GLB → UniRig → FBX
  3. Send FBX + prompt → HY-Motion → Animated FBX
- Progress indicators in UI
- Error handling

---

## Acceptance Criteria

- [ ] Full pipeline works end-to-end from app
- [ ] Can download final animated FBX
- [ ] Handles cold starts gracefully

---

## Notes

- This is where everything comes together
- Cold start handling is important for UX (RunPod serverless has spin-up time)
- Consider caching intermediate results (GLB, rigged FBX) for iteration
