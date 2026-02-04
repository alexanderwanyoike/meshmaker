# Card 4: Tauri App Scaffold

**Status:** Not Started
**Size:** Medium (~2-3 days)
**Dependencies:** Card 0 (can be parallel with container cards)

---

## Goal

Basic desktop app shell with React frontend.

---

## Tech Stack

- Tauri 2.0
- React + TypeScript
- Tailwind CSS (optional)

---

## Deliverables

- `app/` directory with Tauri project
- 4-step wizard UI (Generate → Rig → Animate → Export)
- File picker for image input
- Basic state management
- NO backend integration yet (mock data)

---

## Acceptance Criteria

- [ ] App builds on Windows/Mac/Linux
- [ ] Can navigate through wizard steps
- [ ] File picker works

---

## Notes

- This is just the UI shell - no actual RunPod integration yet
- Mock data allows frontend development in parallel with containers
- Consider using a step/wizard component library
