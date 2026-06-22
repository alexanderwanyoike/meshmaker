# Implementation Cards

Ordered plan to reshape the codebase to match `../VISION.md` and `../ARCHITECTURE.md`. Each card is a vertical slice with a goal, scope, and acceptance criteria. Do them roughly in order; dependencies are noted per card.

## Now - solid cores, navigable repo
- **01** - Provider abstraction (the spine)
- **02** - Fix the transport ceiling (blocker #1, unblocks the quality bar)
- **03** - Restructure repo into the 5 cores
- **04** - Raise quality defaults (blocker #2)
- **05** - Texture preservation through the rig roundtrip (blocker #3)

## Next - backends that hit the quality bars
- **06** - Add Pixal3D / Hunyuan3D 3.5 as Generate backends
- **07** - Swap Rig backend MIA -> SkinTokens
- **08** - Expose Segment tuning knobs (P3-SAM)
- **09** - Plug in Meshy / Tripo as external providers

## Later - the net-new core + polish
- **10** - Build the Video -> Animation core (QuickMagic style)
- **11** - Looping + foot-contact cleanup (Cascadeur-grade)
- **12** - Addons backlog

## Status legend
Each card starts `Status: TODO`. Update to `IN PROGRESS` / `DONE` as you go. The two quality bars (Meshy-6 meshes, Cascadeur-grade animation) are the acceptance lens for every card.
