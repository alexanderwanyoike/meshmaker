# Git Worktree Guide for CharMaker

A practical guide for parallelizing work using git worktrees.

---

## What Are Worktrees?

Normally you have one folder and switch branches. With worktrees, you have **multiple folders**, each on a different branch, all sharing the same git history.

```
# Traditional (one folder, context switching hell):
charmaker/  →  git checkout feat/trellis
            →  git checkout feat/unirig
            →  git checkout feat/tauri
            →  (crying)

# Worktrees (multiple folders, parallel work):
charmaker/              # dev branch (main worktree)
charmaker-trellis/      # feat/trellis branch
charmaker-unirig/       # feat/unirig branch
charmaker-hymotion/     # feat/hymotion branch
charmaker-tauri/        # feat/tauri branch
```

---

## Setup After Card 0

Once Card 0 (repo restructure) is merged to `dev`:

```bash
# Make sure you're in the main repo and on dev
cd /home/alexander/Code/Games/motion-creator
git checkout dev
git pull

# Create worktrees (they go in sibling directories)
git worktree add ../charmaker-trellis -b feat/trellis
git worktree add ../charmaker-unirig -b feat/unirig
git worktree add ../charmaker-hymotion -b feat/hymotion
git worktree add ../charmaker-tauri -b feat/tauri
```

You'll now have:
```
/home/alexander/Code/Games/
├── motion-creator/        # Your main worktree (dev branch)
├── charmaker-trellis/     # feat/trellis branch
├── charmaker-unirig/      # feat/unirig branch
├── charmaker-hymotion/    # feat/hymotion branch
└── charmaker-tauri/       # feat/tauri branch
```

---

## Running Parallel Claude Sessions

Open separate terminals for each worktree:

```bash
# Terminal 1 - Trellis container
cd /home/alexander/Code/Games/charmaker-trellis
claude

# Terminal 2 - UniRig container
cd /home/alexander/Code/Games/charmaker-unirig
claude

# Terminal 3 - HY-Motion update
cd /home/alexander/Code/Games/charmaker-hymotion
claude

# Terminal 4 - Tauri app
cd /home/alexander/Code/Games/charmaker-tauri
claude
```

Each Claude session works independently on its own branch.

---

## Useful Commands

```bash
# List all worktrees
git worktree list

# See status of all worktrees (run from any worktree)
git worktree list --porcelain

# Remove a worktree when done (after PR merged)
git worktree remove ../charmaker-trellis

# If you need to delete a worktree that has changes
git worktree remove ../charmaker-trellis --force

# Prune stale worktree references
git worktree prune
```

---

## Keeping Worktrees Updated

If `dev` gets updates you need in a worktree:

```bash
# In any worktree
git fetch origin
git rebase dev
# OR
git merge dev
```

---

## Merging Back

Each worktree branch becomes a PR:

```bash
# In the worktree (e.g., charmaker-trellis)
git push -u origin feat/trellis

# Create PR via GitHub or:
gh pr create --base dev --title "Card 1a: Trellis 2 container"
```

After PR merges:
```bash
# Clean up the worktree
cd /home/alexander/Code/Games/motion-creator
git worktree remove ../charmaker-trellis
git branch -d feat/trellis  # delete local branch
```

---

## Things to Know

1. **Worktrees share .git** - Commits in one are visible in all (after fetch)

2. **Can't checkout same branch twice** - Each worktree must be on a unique branch

3. **Each needs its own deps** - If using node_modules, venv, etc., each worktree needs its own install

4. **IDE support** - Open each worktree as a separate project/window

5. **.notes is shared** - Since all worktrees branch from dev, they all have these planning docs

---

## Workflow Summary

```
1. Finish Card 0, merge to dev
          ↓
2. Create 4 worktrees from dev
          ↓
3. Open 4 terminals with Claude in each
          ↓
4. Work in parallel (containers don't conflict)
          ↓
5. Push branches, create PRs
          ↓
6. Merge PRs to dev
          ↓
7. Remove worktrees, clean up branches
          ↓
8. Card 5 (integration) in main worktree
```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Create worktree | `git worktree add ../folder-name -b branch-name` |
| List worktrees | `git worktree list` |
| Remove worktree | `git worktree remove ../folder-name` |
| Update from dev | `git fetch && git rebase dev` |
| Push branch | `git push -u origin branch-name` |
