# alibre-py-gear-addon — Code Review (Correctness)

**Date:** 2026-06-20
**Scope:** Second-opinion review, code only (correctness bugs).

**Summary: 1 bug — 1 High**

## High

- **`source/scripts/Template.py:297`** — Integer division in the internal-gear `external_arc` loop. The line reads `t = i / (num_points[3] - 1)`, unlike every other interpolation loop in the file (lines 121, 141, 165, 178, 255, 270, 282, 288) which all use `float(i) / (...)`. AlibreScript runs on **IronPython 2.7** and there is no `from __future__ import division`, so `i / (num_points[3] - 1)` performs **integer division**: `t` is `0` for every iteration except the last (where it is `1`). All but one `external_arc` point therefore collapse onto `theta_arc = start_angle_external`, so the external arc of the internal gear is generated with effectively a single distinct point instead of being swept across the intended angular range. This produces a malformed/degenerate external arc geometry for internal gears. Fix: `t = float(i) / (num_points[3] - 1)`.

## Items reviewed and cleared (not bugs)

- The other interpolation loops correctly use `float(i)`, so they are unaffected.
- `NumericUpDown.Value` assignments that precede `Minimum`/`Maximum` (lines 687–723) happen to fall within the default 0–100 range, so no silent clamping occurs.
- The `num_points[2] // 2` halving for the internal lower arcs (line 280) works for the only call sites, which all use the defaults; passing `num_points[2] < 2` would raise `IndexError` at line 417, but no caller does this.
- `Path.Combine` in `AlibreAddOn.vb` (lines 74/99) is given an already-rooted path; .NET `Path.Combine` correctly returns the rooted second argument, so script resolution still works.
- The session-selection fallback (`AlibreAddOn.vb:60-65`) picking the first session is intentional defensive behavior, not a defect.

No other correctness bugs (null/None dereferences, off-by-one, wrong operators, resource leaks, exception swallowing that hides real failures) were found with confidence.

---

## Fixes applied — 2026-06-20

- **[High] `source/scripts/Template.py:297`** — `t = i / (num_points[3] - 1)` → `t = float(i) / (num_points[3] - 1)`. Confirmed it was the only unwrapped int/int instance in the file.

*Caveat: change applied to source; not verified by build.*
