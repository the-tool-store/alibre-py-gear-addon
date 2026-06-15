# Code Review — alibre-py-gear-addon

- **Date:** 2026-06-15
- **Branch:** `review/2026-06-15-code-review` (branched from `the-tool-store` @ `5cc7e6a` "cleanup push")
- **Reviewer:** Claude (Opus 4.8)
- **Scope:** Full repository review (VB.NET add-on host + IronPython gear-generation scripts + project/solution tooling + submodules)

---

## 1. Summary

This is an Alibre Design add-on that adds a ribbon command ("py-gear Tool") which dynamically
runs an IronPython script (`Template.py`) to generate parametric involute spur gears (external and
internal) on a user-selected plane. The VB.NET layer (`AlibreAddOn.vb`) is the COM-facing host that
embeds an IronPython 2.7 engine; the Python layer (`source/scripts/`) does the gear math and puts up
a WinForms parameter dialog. The gear geometry math (involute/trochoid/arc generation) is ported
from the upstream `py-gear` submodule.

The repository is small (~7 tracked source files, ~930 LOC of real logic, almost all of it in
`Template.py`). The host plumbing is reasonable and noticeably cleaner than the sibling
`alibre-shapes-addon` (it resolves the Alibre install path at runtime via the loaded `AlibreX.dll`
location, and the `.vbproj` correctly copies both `alibre_setup.py` and `Template.py` to output).
However there are real defects: an **integer-division bug** that degrades internal-gear geometry,
the **host carefully injects `CurrentSession`/`CurrentPart` but `Template.py` throws it away** and
re-grabs `TopmostSession` (so gears can land in the wrong document), **hard-coded version-pinned
absolute Alibre paths** in the project file and launch settings, **uninitialized/dirty git
submodules**, and a fair amount of dead/confusing code (a fully-built second `create_gear_with_plane`
that is never used, an empty `RootNamespace`, etc.).

**Overall:** A functional prototype with solid host plumbing but several correctness and
portability issues in the Python layer and project files. Address the High items before shipping.

### Findings by severity

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High     | 4 |
| Medium   | 5 |
| Low / Nit| 7 |

---

## 2. Critical

None. The build is wired correctly (both scripts are copied to output, the install path is
resolved at runtime) and there is no committed binary artifact, so nothing is outright broken at
the build/packaging level.

---

## 3. High

### H-1. Integer (floor) division corrupts the internal-gear `external_arc` sampling
**File:** [Template.py:296-297](../source/scripts/Template.py#L296)

```python
for i in range(num_points[3]):
    t = i / (num_points[3] - 1)          # <-- integer division in IronPython 2.7
    theta_arc = start_angle_external + t * (end_angle_external - start_angle_external)
```

The engine is IronPython **2.7.10** ([vbproj:30](../source/alibre-py-gear-addon.vbproj#L30)) and the
scripts do **not** `from __future__ import division`. In Python 2 `i / (num_points[3] - 1)` is
floor division of two ints, so `t` is `0` for every `i` except the last (`num_points[3]-1`), where
it becomes `1`. Every other curve in both profile generators correctly uses `t = float(i) / (...)`
(e.g. [Template.py:121](../source/scripts/Template.py#L121),
[256](../source/scripts/Template.py#L256), [270](../source/scripts/Template.py#L270),
[282](../source/scripts/Template.py#L282)). This one was missed. The result is that all but the
endpoints of the internal-gear external arc collapse onto `theta = start_angle_external`, producing
a degenerate B-spline.

**Fix:** `t = float(i) / (num_points[3] - 1)` (or add `from __future__ import division` at the top of
the file and audit the other integer divisions such as `num_points[2]//2`).

### H-2. `Template.py` discards the host-provided session and uses `TopmostSession`
**Files:** [Template.py:38-50](../source/scripts/Template.py#L38) vs
[alibre_setup.py:7-12](../source/scripts/alibre_setup.py#L7),
[AlibreAddOn.vb:104-111](../source/AlibreAddOn.vb#L104)

`ScriptRunner1.ExecuteScript` carefully injects the active session into the script scope and runs
`alibre_setup.py`, which builds `CurrentPart` from it:

```vb
scope.SetVariable("CurrentSession", session)
...
_engine.ExecuteFile(setupScriptPath, scope)   ' sets CurrentPart from CurrentSession
_engine.ExecuteFile(mainScriptPath, scope)
```

```python
# alibre_setup.py
if CurrentSession and isinstance(CurrentSession, AlibreX.IADPartSession):
    CurrentPart = Part(CurrentSession)
```

But `Template.py` never uses `CurrentPart`. Instead it re-acquires its own root and part:

```python
alibre = Marshal.GetActiveObject("AlibreX.AutomationHook")
root = alibre.Root
MyPart = Part(root.TopmostSession)
```

`TopmostSession` is not necessarily the session the menu command was invoked on (and the
`SelectionListBox` at [Template.py:553](../source/scripts/Template.py#L553) independently grabs
`Root.TopmostSession` again). If multiple documents are open, the gear and the plane picker can
target the wrong document, and if the topmost session is an assembly, `Part(...)` will fail.
Use the `CurrentPart` that `alibre_setup.py` already prepared (and bail out cleanly if it is `None`,
which the existing `if MyPart is None` guard at [Template.py:636](../source/scripts/Template.py#L636)
would then handle correctly).

### H-3. Hard-coded, version-pinned Alibre install path in the project & launch settings
**Files:** [alibre-py-gear-addon.vbproj:36,40,44](../source/alibre-py-gear-addon.vbproj#L36),
[My Project/launchSettings.json:8](../source/My%20Project/launchSettings.json#L8)

```xml
<HintPath>C:\Program Files\Alibre Design 28.1.1.28227\Program\AlibreAddOn.dll</HintPath>
<HintPath>C:\Program Files\Alibre Design 28.1.1.28227\Program\Addons\AlibreScript\AlibreScriptAddOn.dll</HintPath>
<HintPath>C:\Program Files\Alibre Design 28.1.1.28227\Program\AlibreX.dll</HintPath>
```

```json
"executablePath": "C:\\Program Files\\Alibre Design 28.1.1.28227\\Program\\Alibre Design.exe"
```

These pin the build to one exact Alibre version and the default `Program Files` location. Anyone
on a different version/install path cannot compile or F5-debug without editing the project. (Credit
where due: the *runtime* code does the right thing —
[AlibreAddOn.vb:87](../source/AlibreAddOn.vb#L87) derives the install root from the loaded
`AlibreX.dll` location rather than hard-coding it.) Consider an MSBuild property / env var
(e.g. `$(AlibreInstallDir)`) for the `HintPath`s with the pinned path only as a fallback, and resolve
the launch executable similarly.

### H-4. Git submodules are uninitialized and the recorded pointer is dirty
**Files:** [.gitmodules:1-6](../.gitmodules#L1), submodule tree state

`git submodule status` shows:

```
+bb2ed4e... submodules/alibre-script-adk (heads/main)   # '+' = checked-out commit != recorded
-ed86856... submodules/py-gear                          # '-' = not initialized
```

`submodules/py-gear` is empty (never initialized) and `submodules/alibre-script-adk` is checked out
at a commit that differs from the gitlink recorded in the index, *and* is marked `-dirty`
(`git diff` shows `bb2ed4e...-dirty`). The working tree therefore has an uncommitted submodule
pointer change (`git status` shows `M submodules/alibre-script-adk`). Since `Template.py` is a port
of the `py-gear` math, an uninitialized/divergent submodule makes the provenance of the gear math
unverifiable and a fresh clone incomplete. Re-sync the submodules to a clean recorded commit
(`git submodule update --init --recursive`), commit the corrected pointer, and confirm there is no
local dirty state in the submodule.

---

## 4. Medium

### M-1. `mainScriptFileName` is passed as a full path, making `ScriptFileName` wrong and the second `Path.Combine` redundant
**Files:** [AlibreAddOn.vb:74](../source/AlibreAddOn.vb#L74),
[AlibreAddOn.vb:99,105](../source/AlibreAddOn.vb#L99)

`InvokeCommand` calls:

```vb
runner.ExecuteScript(session, Path.Combine(scriptsPath, "Template.py"))   ' full absolute path
```

but `ExecuteScript` treats the argument as a bare file name and recombines it:

```vb
Dim mainScriptPath As String = Path.Combine(ScriptsPath, mainScriptFileName)   ' line 99
scope.SetVariable("ScriptFileName", mainScriptFileName)                        ' line 105
```

It only *works* because `Path.Combine(dir, absolutePath)` returns the absolute path unchanged. But
(a) the `Path.Combine` at line 99 is misleading dead logic, and (b) `ScriptFileName` is set to the
**full path** rather than `"Template.py"`, which is surely not the intent of a variable named
`ScriptFileName`. Pass just `"Template.py"` from `InvokeCommand`, or change `ExecuteScript` to take
a full path and stop recombining. Pick one contract and make both sides agree.

### M-2. Dead, fully-built duplicate gear-creation paths
**Files:** [Template.py:437-471](../source/scripts/Template.py#L437),
[Template.py:816-850](../source/scripts/Template.py#L816)

`create_gear_with_plane` (lines 437-471) is a complete function that is never called — the button
handler instead defines a *nested* `create_gear_with_unique_name` (lines 817-850) that duplicates
its entire body almost verbatim (parameter creation, `Regenerate`, etc.), differing only in the
sketch name and the `undercut_auto_suppress=optimal_profile_shift` argument. There is also a dead
`original_create = create_gear_with_plane` assignment at
[Template.py:816](../source/scripts/Template.py#L816) that is never used. This is ~35 lines of
copy-paste that will drift out of sync. Delete `create_gear_with_plane` (and the `original_create`
line) or refactor the nested function to call a single shared helper that takes the sketch name and
undercut flag as parameters.

### M-3. `optimal_profile_shift` checkbox is read but the external gear ignores `profile_shift`/`undercut` interaction inconsistently; "Optimal" only suppresses undercut
**File:** [Template.py:98-101](../source/scripts/Template.py#L98),
[Template.py:794,825,832](../source/scripts/Template.py#L794)

The dialog presents both a numeric "Profile Shift (mm)" and an "Optimal profile shift" checkbox.
When the checkbox is on, `undercut_auto_suppress=True` is passed, and the generator *overwrites* the
user's `profile_shift` ([Template.py:99-100](../source/scripts/Template.py#L99)):

```python
if undercut_auto_suppress:
    if base_radius > pitch_radius - m:
        profile_shift = base_radius - (pitch_radius - m)
```

So the user-entered profile shift is silently discarded whenever "Optimal" is checked, with no UI
indication. Additionally the label says "Profile Shift (mm)" but the value is used as an additive
length on the radius, not the dimensionless ISO profile-shift coefficient `x` (which would be
multiplied by `m`). Either honor the entered value, disable the numeric field when "Optimal" is
checked, or clarify the units/semantics. These are engineering values where the mismatch produces a
quietly wrong gear.

### M-4. `SubMenuItems` returns `Nothing` for unknown ids
**File:** [AlibreAddOn.vb:122-127](../source/AlibreAddOn.vb#L122)

```vb
Public Function SubMenuItems(menuId As Integer) As Array ...
    If menuId = ROOT_ID Then
        Return New Integer() {CMD}
    End If
    Return Nothing
End Function
```

Returning `Nothing` (vs an empty array) to a COM host that may enumerate it risks an NRE across the
COM boundary. Return `Array.Empty(Of Integer)()` (or `New Integer() {}`) for the non-root case.

### M-5. `MenuItemState` always returns `ADDON_MENU_ENABLED` regardless of context
**File:** [AlibreAddOn.vb:135-137](../source/AlibreAddOn.vb#L135)

```vb
Public Function MenuItemState(menuId As Integer, sessionIdentifier As String) As ADDONMenuStates ...
    Return ADDONMenuStates.ADDON_MENU_ENABLED
End Function
```

The tool only works in a Part session (it calls `MyPart.AddSketch`), yet the command is enabled even
with no document open or in an assembly/drawing. The script does guard with
`if MyPart is None` ([Template.py:636](../source/scripts/Template.py#L636)), but a better UX is to
disable/grey the command when the active session is not a part. Inspect `sessionIdentifier` /
the active session type and return `ADDON_MENU_DISABLED` when it is not a part session.

---

## 5. Low / Nits

### L-1. Empty `<RootNamespace>` plus a module named `AlibreAddOn` colliding with `Imports AlibreAddOn`
[alibre-py-gear-addon.vbproj:4](../source/alibre-py-gear-addon.vbproj#L4) sets
`<RootNamespace></RootNamespace>` (empty), and [AlibreAddOn.vb:3,9](../source/AlibreAddOn.vb#L3)
both imports the SDK namespace `AlibreAddOn` and declares `Public Module AlibreAddOn` inside
`Namespace AlibreAddOnAssembly`. The empty root namespace is unusual (relies entirely on the
explicit `Namespace` block) and the module-vs-namespace name clash is the kind of ambiguity that
bites later. Set a real `RootNamespace` and rename the module (e.g. `AddOnEntryPoint`).

### L-2. Unused imports and no-op helper in the Python scripts
[Template.py:8](../source/scripts/Template.py#L8) `import time` is never used.
[Template.py:9-11](../source/scripts/Template.py#L9) `printTraceBack()` is an empty stub that just
`return`s, yet it is called with `include_trace=True` throughout `show_error` — so no traceback is
ever actually produced despite the flag. Either implement it (`traceback.format_exc()` into the
message) or drop the parameter.

### L-3. `scale_size` ignores its `scale_factor` argument
[Template.py:481-482](../source/scripts/Template.py#L481):

```python
def scale_size(base_size, scale_factor=1.0):
    return int(base_size)
```

The `scale_factor` parameter is dead (the body never multiplies by it), so any DPI-scaling intent is
not implemented. Remove the parameter or apply it.

### L-4. `MyPart` is mutated as a module global but declared as a local-looking name
[Template.py:37](../source/scripts/Template.py#L37) sets `MyPart = None` at module scope and several
functions (`create_gear_with_plane`, `create_gear_with_unique_name`, `show_gear_form`) read it as a
free variable. This works in the flat script scope but is fragile; passing `MyPart` (or
`CurrentPart` per H-2) explicitly would make the data flow clear and testable.

### L-5. Commented-out success dialog and inconsistent feedback
[Template.py:861](../source/scripts/Template.py#L861) leaves a commented-out
`#show_info("Gear '%s' created successfully!" ...)`. After a successful create the user gets no
confirmation (the form just closes or resets). Either restore a lightweight confirmation or remove
the dead comment.

### L-6. `.adc` Copyright field crams a second project URL into the value with a `|` delimiter
[alibre-py-gear-addon.adc:3](../source/alibre-py-gear-addon.adc#L3):

```xml
<Copyright>Copyright (c) 2025 Stephen S. Mitchell|https://github.com/Eymeric65/py-gear</Copyright>
```

The pipe-joined upstream attribution is non-standard for this field and will render oddly in
Alibre's add-on manager. Put the upstream credit in `Description` or the README and keep `Copyright`
to a clean copyright line. (The attribution itself is good practice — just not in this field.)

### L-7. `documentation/` is an empty placeholder; README claims it is the "primary repository guide"
[.github/README.md:34](../.github/README.md#L34) tells users to rely on `documentation/`, but the
directory contains only `.gitkeep`. Either add the promised notes or soften the README claim.

---

## 6. What looks good

- **Runtime path resolution done right.** Unlike the pinned `HintPath`s, the script engine derives
  the Alibre install root from the loaded `AlibreX.dll` location
  ([AlibreAddOn.vb:87](../source/AlibreAddOn.vb#L87)) and adds the AlibreScript `PythonLib`
  search paths — portable across install locations at runtime.
- **Both Python files are copied to output.** The `.vbproj` includes `alibre_setup.py` *and*
  `Template.py` as `Content` with `CopyToOutputDirectory`
  ([vbproj:22-27](../source/alibre-py-gear-addon.vbproj#L22)), avoiding the
  "setup script missing from output" failure seen in the sibling repo.
- **Robust session lookup.** `InvokeCommand` matches the session by identifier and falls back to the
  first session, all wrapped in try/catch ([AlibreAddOn.vb:48-68](../source/AlibreAddOn.vb#L48)).
- **No committed build artifacts.** `git ls-files` is clean — no `bin/`, `obj/`, or `.exe` in the
  index, and `.gitignore` is comprehensive.
- **Defensive Python UI code.** The `safe_try` wrapper, `show_error`/`show_info` helpers, and the
  timer-based plane `SelectionListBox` are carefully guarded so a UI exception does not crash the
  host.
- **Solid attribution** of the upstream `py-gear` project in both the `.adc` and `.gitmodules`.

---

## 7. Recommended fix order

1. **H-1** — one-line float fix; restores correct internal-gear geometry. (highest value/effort)
2. **H-2** — use the injected `CurrentPart` instead of `TopmostSession` so gears land in the right
   document and assembly sessions fail gracefully.
3. **H-4** — re-init and clean the submodules so a fresh clone builds and the gear-math provenance is
   verifiable; commit the corrected pointer.
4. **H-3** — unpin the Alibre version/path in `.vbproj` and `launchSettings.json`.
5. **M-1 / M-3** — fix the `ScriptFileName`/`Path.Combine` contract and clarify the profile-shift vs
   "Optimal" semantics.
6. **M-2** — delete the duplicate gear-creation code.
7. Sweep **M-4 / M-5 / L-*** when next touching the host and scripts.
