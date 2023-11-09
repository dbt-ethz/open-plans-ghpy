"""
    Remarks:
        Author: 
        License:
        Version: 
"""
import urllib2
from urllib2 import HTTPError, URLError
import json
from collections import OrderedDict

from ghpythonlib.componentbase import executingcomponent as component
import Rhino
import scriptcontext
import Grasshopper.Kernel as gh
import Rhino.Geometry as rg
import ghpythonlib.treehelpers as th

scriptcontext.doc = Rhino.RhinoDoc.ActiveDoc

BASE_URL = "https://open-plans.herokuapp.com/"


def get_data(dict, key):
    if dict['succeeded']:
        return dict.get(key)
    else:
        error_message = dict.get('error', 'Failed without error message')
        print(error_message)
        
def make_request(url):
    try:
        response = urllib2.urlopen(url)
        json_string = response.read().decode('utf-8')
        return dict(json.loads(json_string))
    except HTTPError as e:
        ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, "HTTP Error: {}".format(e.code))
        return {"succeeded": 0, "error": "HTTP Error: {}".format(e.code)}
    except URLError as e:
        ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, "URL Error: {}".format(e.reason))
        return {"succeeded": 0, "error": "URL Error: {}".format(e.reason)}
    except Exception as e:
        ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, "An error occurred: {}".format(e))
        return {"succeeded": 0, "error": "An error occurred: {}".format(e)}

def fetch_plan(plan_id):
    url = BASE_URL + 'plan/fetch/{}'.format(plan_id)
    return make_request(url)

def filter_fetch_polygons(number, page, text=None, year_domain=None):
    if number > 100:
        number = 100
    params = {}
    if text is not None:
        text_modified = text.replace('\r\n', '')
        params['search'] = text_modified.replace(' ', '%20')
    if year_domain is not None:
        params['year_from'] = int(year_domain[0])
        params['year_to'] = int(year_domain[1])
    if number is not None:
        params['number'] = int(number)
    if page is not None:
        params['page'] = int(page)
    
    query_string = '&'.join(['{}={}'.format(key, value) for key, value in params.items()])
    url = BASE_URL + 'polygon/fetch/filter?{}'.format(query_string)
    return make_request(url)


class OpenPlansItem:
    
    def __init__(self, data):
        self.height_mm = data['height_mm']
        self.building_outline = self.building_outline_pts_to_rhino_geom(points=data['points'])
        self.name = data['name']
        self.architects = data['architects']
        self.civil_engineers = data['civil_engineers']
        self.description = data['description']
        self.year_of_completion = data['year_of_completion']
        self.floor_area = self.get_polygon_area()
        self.floors = data['floors']
        self.level = data['floor']
        self.geolocation = self.format_geolocation(data['geolocation'])
        self.height = data['height']
        self.projectURL = 'https://plans.arch.ethz.ch/#/project/{}'.format(data['project_id'])

            
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
        return list([coordinate[0], coordinate[1]*-1 + self.height_mm])
    
    @staticmethod
    def format_geolocation(data):
        if data:
            try:
                point_str = data.replace('POINT(', '').replace(')', '')
                longitude, latitude = point_str.split(' ')
                return '{}  {}'.format(latitude, longitude)
            except:
                return None
        return None



class OpenPlansSearchFilter(component):

    def RunScript(self, textFilter, yearOfCompletionFilter, numberOfPlans):
        
        
        if not numberOfPlans:
            numberOfPlans = 10

        if textFilter or yearOfCompletionFilter:
            plandata = filter_fetch_polygons(number=numberOfPlans, page=0, text=textFilter, year_domain=yearOfCompletionFilter)
            if plandata['succeeded'] == 0:
                ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, "No plans found with search filter")
                return None, None, None
                
            plans = [OpenPlansItem(data=p) for p in plandata['plans']]
            if plans:
                projects = [OrderedDict((key, value) for key, value in item.__dict__.items() if key != 'height_mm') for item in plans]
                properties = th.list_to_tree( [p.values() for p in projects] )
                propertyNames = projects[0].keys()
            
                return projects, properties, propertyNames 
            
            else:
                raise Exception(' Not able to fetch projects from open plans ')
        
        else:
            return None, None, None