"""
Retrieve floor plans from the Open Plans database with a geometircal search.
    Inputs:
        searchShape:    Closed Polyline that represents the desired shape of retrieved floor plans.
                        {item, polyline}
        numberOfPlans:  (optional: default is 20) Set this value to specify the number of plans 
                        returned from the database.
                        {item, int)


    Output:
        projects:       List of open plans projects as dictionaries (not readable by Grasshopper)
                        {list, dict}
        properties:     Property values from open plans projects (readable by Grasshopper in tree structure)
                        {item, list}
        propertyNames:  Property names from open plans projects (readable by Grasshopper in list)
                        {item, list}

    
    Remarks:
        Author: 
        License:
        Version: 
"""

# PYTHON LIBRARY IMPORTS
import urllib2
import json
import os

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper
import GhPython
import Rhino
import Rhino.Geometry as rg
import Rhino.Display as rd
import scriptcontext



# PYTHON LIBRARY IMPORTS
import urllib2
from urllib2 import HTTPError
import json
import os

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper
import GhPython
import Rhino
import Rhino.Geometry as rg
import Rhino.Display as rd
import scriptcontext
import ghpythonlib.treehelpers as th
from ghpythonlib.componentbase import executingcomponent as component


class OpenPlansSearch:

    def __init__(self, search_shape, number_of_plans):
        self.searchShape = search_shape
        self.numberOfPlans = number_of_plans if number_of_plans else 20
        self.uri = "https://open-plans.herokuapp.com/"
        self.similarPlans = self.api_search_by_shape()
        self.openPlansItems = []
        
    def api_search_by_shape(self):
        url = self.uri + 'searchbyshape?number={}'.format(self.numberOfPlans)
        req = urllib2.Request(url, self.search_shape_to_polygon(), headers={'Content-Type': 'application/json'})
    
        try:
            response = urllib2.urlopen(req)
            json_string = response.read().decode('utf-8')
            ret_val = dict(json.loads(json_string))
            if ret_val['succeeded']:
                if len(ret_val) == 0:
                    raise Exception(" No plans are retrieved from the database ")
                return ret_val['similar_plan_list']
        except HTTPError as e:
            raise Exception(e)
            
    def search_shape_to_polygon(self):
        polygon = self.format_polygon(x_coords=[x for x in self.searchShape.X], y_coords=[y*-1 for y in self.searchShape.Y])
        return json.dumps(polygon)
    
    @staticmethod
    def format_polygon(x_coords, y_coords):
        return {'polygon': [{'x': x, 'y': y} for x, y in zip(x_coords, y_coords)]}
        
    def get_open_plans_items(self):
        self.openPlansItems = [OpenPlansItem(data=p) for p in self.similarPlans]


class OpenPlansItem:
    
    def __init__(self, data):
        self.building_outline = self.building_outline_pts_to_rhino_geom(points=data['points'])
        self.name = data['name']
        self.architects = data['architects']
        self.civil_engineers = data['civil_engineers']
        self.description = data['description']
        self.year_of_completion = data['year_of_completion']
        self.floor_area = self.get_polygon_area()
        self.floors = data['floors']
        self.floor = data['floor']
        self.geolocation = self.format_geolocation(data['geolocation'])
        self.height = data['height']
        self.image_path = data['image_path']
        self.project_id = data['project_id']
        self.plan_id = data['plan_id']
            
    def get_polygon_area(self):
        try:
            props = rg.AreaMassProperties.Compute(self.building_outline)
            return props.Area * 10**-6
        except:
            return None
          
    def building_outline_pts_to_rhino_geom(self, points):
        if points[0] != points[-1]:
            points.append(points[0])
        pts = map(self.transform_to_rhino_coords, points)
        polyline = rg.Polyline()
        for pt in pts:
            polyline.Add(rg.Point3d(pt[0], pt[1], 0))
        polylineCrv = polyline.ToPolylineCurve()
        return polylineCrv

    def transform_to_rhino_coords(self, coordinate):
        return list([coordinate[0], coordinate[1]*-1])
    
    @staticmethod
    def format_geolocation(data):
        if data:
            return '{}, {}'.format(data['latitude'], data['longitude'])
        return None


class OpenPlansGH(component):

    def RunScript(self, searchShape, numberOfPlans):

        if not searchShape:
            return None, None, None

        if searchShape.IsValid and searchShape.IsClosed:

            op = OpenPlansSearch(searchShape, number_of_plans=numberOfPlans)
            
            if op.similarPlans:
                op.get_open_plans_items()
            else:
                raise Exception(' Not able to fetch projects from open plans ')
            
            if op.openPlansItems:
                projects = [item.__dict__ for item in op.openPlansItems]
                properties = th.list_to_tree( [p.values() for p in projects] )
                propertyNames = projects[0].keys()
            
            return projects, properties, propertyNames 
        
        else:
            raise Exception(' searchShape; polyline is not valid/closed ')