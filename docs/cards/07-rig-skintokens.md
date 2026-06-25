# Card 07 - Swap Rig backend MIA -> SkinTokens

Status: DEFERRED
Depends on: 01 (provider abstraction)
Quality bar: enables better rigs (feeds the Cascadeur-grade animation bar)

## Goal

Add SkinTokens / TokenRig as a Rig provider for higher-quality skeletons and skinning.

## Why

SkinTokens (successor to UniRig, Feb 2026) reports 98-133% skinning-accuracy and 17-22% bone-prediction improvement over prior SOTA. Better skinning means cleaner deformation, which means less manual cleanup in Cascadeur. See REFERENCE section 2.

## Scope

- New container `containers/skintokens/` implementing the Rig contract (mesh -> URL to rigged FBX).
- Register as a Rig provider alongside MIA.
- **Critical compatibility check:** does SkinTokens' output skeleton map into HY-Motion's `retarget_fbx.py` (700+ entry SMPL-H -> Mixamo dict)? If it does not output Mixamo bone names, either add a bone mapping or a retarget adapter. This was exactly why UniRig was dropped in favour of MIA - do not repeat it.

## Acceptance criteria

- A mesh rigged via SkinTokens animates correctly through the existing Motion retarget path.
- Side-by-side: SkinTokens vs MIA deformation quality on a test character.
- MIA remains available as a fallback (and for the humanoid-only fast path).

## Notes

If SkinTokens' skeleton is non-Mixamo, the retarget adapter is the real work in this card, not the container.
