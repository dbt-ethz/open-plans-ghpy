"""
    Remarks:
        Author: 
        License:
        Version: 
"""
import urllib2
from urllib2 import HTTPError
import json
import cookielib
import copy

from ghpythonlib.componentbase import executingcomponent as component
import scriptcontext as rs
import Grasshopper.Kernel as gh

BASE_URL = "https://open-plans.herokuapp.com/"

rs.sticky['resp'] = {'succeeded': 0, 'error':''}

PROJECT_UPLOAD = {
    'id': None,
    'name': None,
    'plans': []
}

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

def save_project(project):
    url = BASE_URL + 'project/save'
    data = json.dumps(project)
    print(data)
    req = urllib2.Request(url, data=data, headers={
                          'Content-Type': 'application/json'})

    try:
        response = urllib2.urlopen(req)
        json_string = response.read().decode('utf-8')
        retVal = dict(json.loads(json_string))
        return retVal
    except HTTPError as e:
        if e.code == 403:
            return {"succeeded": 0, "error": "You are not logged in or your account has no rights to edit this project."}
        else:
            return {"succeeded": 0, "error": "HTTP Error: {}".format(e.code)}

def fetch_project(project_id):
    url = BASE_URL + 'project/fetch/{}'.format(project_id)
    return make_request(url)

def get_polygon_ids(plan_dict):
    return [ p['id'] for p in plan_dict['polygons'] ]

class OpenPlansExport(component):

    def RunScript(self, OpenPlansPlan, export, keepExistingPolygons=False):

        if OpenPlansPlan:
            print(keepExistingPolygons)
            data_fields=copy.deepcopy(PROJECT_UPLOAD)
            project = fetch_project(project_id=OpenPlansPlan.project_id)
            plan = fetch_plan(plan_id=OpenPlansPlan.plan_id)
            polygon_ids = get_polygon_ids(plan_dict=plan['plan'])
            data_fields['id'] = OpenPlansPlan.project_id
            data_fields['name'] = project['project']['name']
            plan_data = OpenPlansPlan.remove_empty_values()
            plan_data['deleted_polygon_ids'] = polygon_ids
            if keepExistingPolygons is True:
                plan_data['deleted_polygon_ids'] = []
                
            data_fields['plans'].append(plan_data)
            if export:
                resp = save_project(project=data_fields)
                rs.sticky['resp'] = resp
            
            if rs.sticky['resp']['succeeded']:
                return "Thank you! Your plan is succesfully saved to Open Plans. Check it out here: https://plans.arch.ethz.ch/#/plan/{}".format(data_fields['plans'][0]['id'])
            else:
                print(rs.sticky['resp']['error'])
                ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, rs.sticky['resp']['error'])
                return rs.sticky['resp']['error']
            
