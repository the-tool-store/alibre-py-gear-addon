# Alibre Py-Gear Add-On

An Alibre Design add-on that generates parametric involute spur gear sketches on a selected plane in the active part.

It registers a py-gear menu in Alibre Design. The menu opens a dialog where you set the gear parameters and pick a plane in the workspace. The add-on then draws the gear sketch on that plane.

A VB.NET assembly hosts an IronPython engine and runs the gear scripts. The project targets Alibre Design 29.x (built and referenced against 29.0.0.29060), .NET Framework 4.8.1, and IronPython 2.7.10. It depends on Alibre's AlibreScript add-on for the API and Python libraries.

## Table Of Contents

- [What Is Here](#what-is-here)
- [Official Alibre Resources](#official-alibre-resources)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Key Files](#key-files)
- [Key Folders](#key-folders)
- [Notes](#notes)
- [License](#license)

## What Is Here

- A VB.NET add-on (`source/AlibreAddOn.vb`) that registers the py-gear menu and hosts an IronPython script engine.
- An IronPython gear generator (`source/scripts/Template.py`) with a Windows Forms dialog and the involute/trochoid geometry math.
- A setup script (`source/scripts/alibre_setup.py`) that resolves the active part or assembly session before the main script runs.
- The add-on manifest, Visual Studio solution, and project file under `source/`.
- Git submodules for the py-gear geometry source and the alibre-script-adk kit.

Capabilities of the gear generator:

- Generates external and internal involute spur gear sketches.
- Configurable parameters: number of teeth, module, pressure angle, profile shift, and (for internal gears) thickness.
- Optional automatic profile shift to suppress undercut on low-tooth-count gears.
- Builds tooth geometry from involute, trochoid root, and addendum/dedendum arc segments.
- Creates each gear on a user-selected plane with a unique sketch name and stores pitch radius and tooth count as part parameters.

## Official Alibre Resources

Alibre's official resources for API development and AI/LLM/agent workflows: <https://www.alibre.com/api/>

## Requirements

- Alibre Design 29.x, built and referenced against Alibre Design 29.0.0.29060.
- Alibre's AlibreScript add-on, installed with Alibre Design. The add-on loads `AlibreScript.API` from the Alibre install's `PythonLib` folder at runtime.
- .NET Framework 4.8.1 (`net481`).
- IronPython 2.7.10 (bundled in the add-on output).
- Windows, x64.

## Quick Start

1. Build `source/alibre-py-gear-addon.vbproj` in the Release configuration.
2. Copy the build output into an Alibre add-ons directory.
3. Start Alibre Design, open a part, and open the **py-gear** menu.

## Installation

1. Build the `source/alibre-py-gear-addon.vbproj` project (or open `source/alibre-py-gear-addon-solution.sln`) in the Release configuration.
2. Copy the build output (the `alibre-py-gear-addon.dll`, the IronPython runtime DLLs, `logo.ico`, the `scripts` folder, and the `alibre-py-gear-addon.adc` manifest) into an Alibre add-ons directory.
3. Start Alibre Design. The `.adc` manifest registers the add-on, which loads at startup and adds a **py-gear** menu.

## Usage

1. Open or create a part in Alibre Design.
2. From the **py-gear** menu, choose **py-gear Tool** to open the gear generator dialog.
3. Set the number of teeth, module, pressure angle, profile shift, and (for internal gears) thickness, then choose External or Internal gear.
4. Click the plane selector, then pick a plane in the workspace.
5. Click **Create Gear** to generate the gear sketch on the selected plane. Enable **Stay open after creating** to create multiple gears in one session.

## Key Files

| File | Purpose |
| --- | --- |
| `source/AlibreAddOn.vb` | Add-on entry point. Registers the py-gear menu, hosts an IronPython engine, and runs the setup and gear scripts. |
| `source/scripts/Template.py` | Gear generator. Builds the Windows Forms dialog and the external/internal involute spur gear geometry. |
| `source/scripts/alibre_setup.py` | Setup script that resolves the current part or assembly session for the main script. |
| `source/alibre-py-gear-addon.vbproj` | Project file targeting `net481` and x64, referencing AlibreX/AlibreAddOn/AlibreScriptAddOn and IronPython 2.7.10. |
| `source/alibre-py-gear-addon-solution.sln` | Visual Studio solution. |
| `source/alibre-py-gear-addon.adc` | Add-on manifest that registers the DLL and icon with Alibre Design. |
| `source/logo.ico` | Menu and add-on icon. |
| `LICENSE` | MIT license. |

## Key Folders

| Folder | Purpose |
| --- | --- |
| `source/` | VB.NET add-on project and IronPython scripts. |
| `source/scripts/` | IronPython scripts copied to the add-on output (`alibre_setup.py`, `Template.py`). |
| `submodules/` | Git submodules: py-gear (gear geometry source) and alibre-script-adk (Alibre Script add-on kit). |
| `documentation/` | Placeholder for documentation. Currently empty. |
| `reviews/` | Dated code-review notes. |
| `.github/` | This README and community health files (issue templates, contributing guide, code of conduct). |

## Notes

- The gear geometry derives from the py-gear project (<https://github.com/Eymeric65/py-gear>), as recorded in the add-on manifest's copyright line.
- Scripts run under IronPython 2.7.10, so they stay Python 2.7 compatible.
- The add-on requires Alibre's AlibreScript add-on. `AlibreAddOn.vb` adds the AlibreScript `PythonLib` paths to the engine's search paths, and `alibre_setup.py` references `AlibreScriptAddOn`.
- The `documentation/` folder holds only a `.gitkeep`, so there are no bundled screenshots yet.

## License

See [LICENSE](../LICENSE).
