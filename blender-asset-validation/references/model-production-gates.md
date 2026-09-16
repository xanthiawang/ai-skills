# Model-first production gates

Applies to reference-driven characters and articulated robots intended for a
real-time engine. A scoped motion study or render-only task need not rebuild an
already suitable asset. Apply gates per asset, not as a blanket delay for the
whole project; explicit user-requested approval gates still apply.

## Production order

1. Establish the authoritative reference, proportions, structural relationships
   and required motions. Inspect the actual current model, not just its preview.
2. Correct the base form and separate moving parts. Define joints, axes, travel,
   clearances and attachment points against that geometry.
3. Add high-poly detail where necessary for silhouette, surface finish or baking.
   A separate high-poly asset is optional when the required finish can be achieved
   directly. Dense image-to-3D output or subdivision alone is not finished high-poly work.
4. Produce and inspect the runtime low-poly mesh/re-topology. Preserve silhouette,
   mechanical boundaries and deformation loops. Freeze proportions, part layout,
   topology and joint locations for the binding revision.
5. From that stable model, work in parallel on UVs -> required baking -> materials,
   and production rig/weights -> bounded motion tests -> formal animations.
6. Integrate the matching model/material/animation revision into the target engine,
   then test on the intended hardware. Export success is not engine/device acceptance.

## Before formal animation

Use the existing work-state/check record; do not create a second checklist.
Record the current model path/revision (or hash), passed gates, evidence and
remaining defects. Require:

- Reference-relative proportions and required structures visually inspected.
- Moving parts separated without dragging the chassis, tearing surfaces, exposing
  unintended holes or moving a fixed panel; relevant pivots and clearances checked.
- A stable runtime mesh suitable for binding, with topology appropriate to its motion.
- Rig/weights verified at rest and critical poses; required parts remain attached.

Before these gates pass, only a small, explicitly labeled mechanism/pose test is
appropriate. Do not batch a full story set, copy old curves to inflate progress,
or count holds/exports/clip names as proof of functional animation. Continue the
needed model corrections rather than inventing a new user-approval dependency.

## Changes invalidate dependent work

If proportions, parts, topology or joints change, recheck the affected UV/bakes,
binding and clips. Skin-weight transfer or retargeting may be useful only when
compatible and verified; it is not automatically a rebuilt or accepted result.
If the user retires old-model animations, do not retain them as valid current
deliverables, silently transplant their rig, or rename copies as rebuilt clips.
Deletion still needs explicit scope and recoverability; this rule is not blanket
permission to delete assets.

Report model, UV/material, binding, diagnostic test, formal animation, engine
integration and hardware acceptance separately. A source `.blend`, a preview,
an FBX/GLB and a clip count establish different facts; none implies all stages passed.
