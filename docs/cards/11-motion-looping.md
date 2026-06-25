# Card 11 - Looping + foot-contact cleanup

Status: TODO (BACKLOG)
Depends on: 03 (motion core)
Quality bar: Cascadeur-grade animation

## Goal

Make Motion output loopable and clean up foot sliding, so walk/run/idle clips are game-usable and a better Cascadeur starting point.

## Why

HY-Motion outputs one-shot, non-looping animations; frame 0 != frame N causes a visible pop. Looping is table stakes for game animation (DeepMotion has it; HY-Motion doesn't). This is a post-processing problem - no model change needed.

## Approach (from prior research)

No Python lib does this out of the box; build it (~175 LOC). Recommended pipeline:

1. **(Optional) prompt hints** - test loop-oriented prompts first; don't rely on them.
2. **Generate ~1.5-2x duration**, then **pose matching** - find two already-similar frames `(i, j)` with `j - i approximately target`, cut there. Pose distance = weighted L2 over joints (emphasise hips/feet) + quaternion distance.
3. **Inertialization** - cubic-decay blend at the cut so frame 0 == frame N in position and velocity. `cubic_decay(x, v, blend_time, t)` with Hermite coefficients guaranteeing `f(0)=x, f(1)=0`.
4. **Root motion mode** - `locked` (idle/dance: zero root XZ), `blend_horizontal` (walk/run), `blend_all` (jumps).
5. **Foot-contact cleanup** - detect planted feet, IK-pin to kill sliding.

Building blocks: numpy, `scipy.spatial.transform` (Rotation/Slerp), `scipy.spatial.distance.cdist`, optionally `dtaidistance` (DTW), `upc-pymotion` for FK/IO. (Full code sketch was in the old `looping-technical-card.md`; recover from git history on `dev` if needed.)

## UI additions

- "Loop" checkbox, loop-mode dropdown (Locked / Blend Horizontal), transition-duration slider.

## Acceptance criteria

- A generated walk cycle loops seamlessly (no pop) with `blend_horizontal`.
- An idle loops in place with `locked`.
- Visibly reduced foot sliding.

## References

- Orange Duck - [Looping Animations](https://theorangeduck.com/page/creating-looping-animations-motion-capture), [Dead Blending](https://theorangeduck.com/page/dead-blending)
- [Inertialization, GDC 2018 (Gears of War)](https://cdn.gearsofwar.com/thecoalition/publications/GDC%202018%20-%20Inertialization%20-%20High%20Performance%20Animation%20Transitions%20in%20Gears%20of%20War.pdf)
- [DeepMotion SayMotion loop tool](https://www.deepmotion.com/post/saymotion-v2-4-loop-refine-rerun)
