"""
    Remarks:
        Author: 
        License:
        Version: 
"""
from ghpythonlib.componentbase import executingcomponent as component


class OpenPlansPlan(component):

    def RunScript(self, OpenPlansPlan, addPolygons):
        
        if addPolygons:
            OpenPlansPlan.clear_polygons()
            for polygon in addPolygons:
                polygon.move_data_pts_to_positive(move_y=OpenPlansPlan.height_mm)
                OpenPlansPlan.add_polygon(polygon.polygon)
    
        return OpenPlansPlan
