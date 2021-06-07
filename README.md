# Open Plans Rhino Grasshopper

Interact with open plans within Rhino/Grasshopper.

#### Implemented features:
- search-by-shape

## Getting started

### Requirements
* [Rhinoceros 3D 6.0/7.0](http://www.rhino3d.com/)

### Installation
1. Download the .ghuser file from grasshopper/components
2. In the grasshopper window, go to `file > special folders > user object folder` then copy the .ghuser file there

## Contributions

### Build components using the command line

Build components using the COMPAS componentizer tool: https://github.com/compas-dev/compas-actions.ghpython_components .

Make sure to have IronPython installed and the `GH_IO.dll` assembly available (e.g. in C:/Program Files/Rhino 7/Plug-ins/Grasshopper)
Then start the script pointing it to a source and target folder, e.g.:

    ipy componentize.py src grasshopper\components --ghio "C:/Program Files/Rhino 7/Plug-ins/Grasshopper"

Optionally, tag it with a version:

    ipy componentize.py src grasshopper\components --ghio "C:/Program Files/Rhino 7/Plug-ins/Grasshopper" --version 0.1.2
