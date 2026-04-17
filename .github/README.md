# alibre-py-gear-addon

> Note: This repository is undergoing significant changes and is currently a work in progress.

| Item | Value |
| --- | --- |
| Type | Alibre add-on / plugin |
| Primary stack | Python, VB.NET, Alibre automation |

## Overview
This repository contains the source and supporting assets for alibre-py-gear-addon, organized under the standardized repository layout.

## Repository Layout
- source/: project source, solution or project files, and runtime assets.
- submodules/: external git submodules used by the repository when required.
- documentation/: supplementary notes, changelogs, and non-GitHub documentation.
- .github/: repository README, templates, and GitHub-specific community files.
- `source/alibre-py-gear-addon-solution.sln`: key source or build entry point.
- `source/alibre-py-gear-addon.adc`: key source or build entry point.
- `source/alibre-py-gear-addon.vbproj`: key source or build entry point.
- `source/scripts/alibre_setup.py`: key source or build entry point.
- `source/scripts/Template.py`: key source or build entry point.
- `LICENSE`: repository license file kept at the root.

## Requirements
- Windows development environment.
- A .NET build environment compatible with the projects under source/.
- Python installed if you need to run or modify the Python components under source/.
- Alibre Design installed if you need to run, debug, or validate the Alibre integration.

## Build and Use
1. Open `source/alibre-py-gear-addon-solution.sln` in your preferred IDE.
2. Restore dependencies and build from the source/ layout.
3. Use the notes in documentation/ and .github/README.md as the primary repository guide.

## Current Limitations
- The repository has been normalized for layout consistency; any path-sensitive tooling should be revalidated against the new folder structure.
- Existing runtime behavior and project-specific limitations remain unchanged.

## License
See [LICENSE](../LICENSE).

