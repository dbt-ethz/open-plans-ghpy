"""
    Remarks:
        Author: 
        License:
        Version: 
"""
import copy
from ghpythonlib.componentbase import executingcomponent as component


class OpenPlansPlanAdd(component):

    def RunScript(self, OpenPlansPlan, addPolygons):
        
        edit_polygons_to_add = []
        
        if addPolygons:
            OpenPlansPlan.clear_polygons()
            edit_polygons_to_add = [ copy.deepcopy(p) for p in addPolygons ]
            
            for polygon in edit_polygons_to_add:

                polygon.move_data_pts_to_positive(move_y=OpenPlansPlan.height_mm)
                
                OpenPlansPlan.add_polygon(polygon.polygon)

        return OpenPlansPlan
