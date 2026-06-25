# Card 04 - Archive old generator quality-default tuning

Status: ARCHIVED
Depends on: 02 (transport ceiling must be gone first)
Quality bar: Meshy-6 meshes

## Goal

Do not spend implementation time tuning Trellis2 or Hunyuan3D 2.1 defaults while the
project is scoped to a single new Generate backend: Hunyuan3D 3.5.

## Why

The old defaults were tuned for the base64 transport limit, but these backends are no
longer the target path. Improving them would make the project broader without making
the MVP clearer.

## Scope

- Leave old Trellis2/Hunyuan3D 2.1 code as reference until Hunyuan3D 3.5 is integrated.
- Do not add Draft / Standard / High presets for the old generators.
- Remove or archive old generator UI once the Hunyuan3D 3.5 path is working.

## Acceptance criteria

- No active task depends on tuning Trellis2 or Hunyuan3D 2.1.
- The active Generate plan points only to card 06.

## Notes

Revisit only if Hunyuan3D 3.5 access fails and an old self-hosted generator must
temporarily become the fallback.
