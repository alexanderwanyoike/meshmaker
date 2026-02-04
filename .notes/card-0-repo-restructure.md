# Card 0: Repo Restructure & Rename

**Status:** Not Started
**Size:** Small (~1 day)
**Dependencies:** None (unlocks all other cards)

---

## Goal

Transform motion-creator into charmaker monorepo structure.

---

## Changes

- Rename repo (GitHub) or create new repo `charmaker`
- Set up monorepo structure:
  ```
  charmaker/
  ├── containers/
  │   └── hymotion/     # Move existing cloud/ here
  ├── app/              # Empty, for Tauri later
  ├── shared/           # Empty, for shared utils
  ├── .notes/           # Keep planning docs
  └── README.md         # New project overview
  ```
- Update README with new vision
- Archive or deprecate old local/ client code

---

## Acceptance Criteria

- [ ] Monorepo structure in place
- [ ] Existing HY-Motion container still builds
- [ ] CI/CD updated for new paths

---

## Notes

- Keep git history by renaming rather than creating new repo
- The `local/` directory contains experimental code that can be archived
