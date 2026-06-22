# Alibre Py-Gear Add-On

An Alibre Design add-on that generates parametric involute spur gear profiles on a selected plane in the active part, driven by a dialog and IronPython.

## Features
- Generates external and internal involute spur gear sketches.
- Configurable parameters: number of teeth, module, pressure angle, and profile shift.
- Optional automatic profile shift to suppress undercut on low-tooth-count gears.
- Builds tooth geometry from involute, trochoid root, and addendum/dedendum arc segments.
- Creates each gear on a user-selected plane with a unique sketch name and stores pitch radius and tooth count as part parameters.

## Requirements
- Alibre Design 29.x (built and referenced against Alibre Design 29.0.0.29060, including the AlibreScript add-on).
- .NET Framework 4.8.1 (net481).
- IronPython 2.7.10 (bundled in the add-on output).

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

## License
See [LICENSE](../LICENSE).
