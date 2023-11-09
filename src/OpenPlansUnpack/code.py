"""
Unpack projects data from Open Plans GH.
    Inputs:
        projects:       List of python dictionaries; output from OpenPlansGH component
                        
    Output:
        properties:     Property values from open plans projects (readable by Grasshopper in tree structure).


    Remarks:
        Author: 
        License:
        Version: 
"""

from ghpythonlib.componentbase import executingcomponent as component
import ghpythonlib.treehelpers as th
from collections import OrderedDict

def is_user_defined_instance(obj):
    return isinstance(obj, object) and not isinstance(obj, (type(None), type, dict, list, tuple, str))

class OpenPlansUnpack(component):

    def RunScript(self, OpenPlansData):
        
        if not OpenPlansData:
            return None

        if type(OpenPlansData) != list:
            raise Exception("OpenPlansData must be of type list")
        
        data = [i.attributes if is_user_defined_instance(i) else i for i in OpenPlansData]

        for i in data:
            if type(i) != dict and not isinstance(i, OrderedDict):
                raise Exception("OpenPlansData must contain python dictionaries")

        properties = th.list_to_tree( [p.values() for p in data] )
        projectFields = data[0].keys()

        return properties, projectFields