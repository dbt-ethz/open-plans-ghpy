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


class OpenPlansUnpack(component):

    def RunScript(self, projects):

        if not projects:
            return None

        if type(projects) != list:
            raise Exception("projects must be of type list")
        
        if type(projects[0]) != dict:
            raise Exception("projects must contain python dictionaries")

        properties = th.list_to_tree( [p.values() for p in projects] )

        return properties