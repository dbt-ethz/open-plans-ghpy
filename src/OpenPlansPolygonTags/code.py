"""
    Remarks:
        Author: 
        License:
        Version: 
"""
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper
import Grasshopper.Kernel.Special.GH_ValueList as vl
from Grasshopper import Instances

tags = [
        "building-outline",
        "balcony",
        "bath",
        "chimney",
        "closet",
        "corridor",
        "dining",
        "elevator",
        "foyer",
        "garden",
        "garage",
        "kitchen",
        "living",
        "room",
        "stair",
        "sleeping",
        "terrace",
        "wc",
      ]

class OpenPlansPolygonTags(component):

    def RunScript(self, create):

        if create:
            # Get the active document
            doc = Instances.ActiveCanvas.Document
            # Create a new GH_ValueList component
            v = vl()
            # Set the list mode to DropDown
            v.ListMode = Grasshopper.Kernel.Special.GH_ValueListMode.DropDown
            # Clear any existing items in the list
            v.ListItems.Clear()
            # Add items to the value list
            for tag in tags:
                v.ListItems.Add(Grasshopper.Kernel.Special.GH_ValueListItem(tag, '"{}"'.format(tag)))
            # Add the value list component to the document
            doc.AddObject(v, False)
