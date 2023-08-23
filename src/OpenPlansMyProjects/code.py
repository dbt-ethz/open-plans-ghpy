"""
    Remarks:
        Author: 
        License:
        Version: 
"""

# PYTHON LIBRARY IMPORTS
import urllib2
from urllib2 import HTTPError, URLError
import json
import cookielib

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper
import Grasshopper.Kernel.Special.GH_ValueList as vl
from Grasshopper import Instances
import Grasshopper.Kernel as gh


BASE_URL = "https://open-plans.herokuapp.com/"


def cookie_processor(func):

    def wrapper(*args, **kwargs):
        cj = cookielib.CookieJar()
        # Use the HTTPCookieProcessor object of the urllib2 library to create a cookie processor
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)

        val = func(*args, **kwargs)
        return val

    return wrapper

def make_request(url, data=None, headers=None):
    if not data:
        req = urllib2.Request(url)
    else:
        req = urllib2.Request(url, data=data, headers=headers)
    
    try:
        response = urllib2.urlopen(req)
        json_string = response.read().decode('utf-8')
        return dict(json.loads(json_string))
    except HTTPError as e:
        return {"succeeded": 0, "error": "HTTP Error: {}".format(e.code)}
    except URLError as e:
        return {"succeeded": 0, "error": "URL Error: {}".format(e.reason)}
    except Exception as e:
        return {"succeeded": 0, "error": "An error occurred: {}".format(e)}

@cookie_processor
def login(email, password):
    url = BASE_URL + 'auth/login'
    data = json.dumps({'email': email, 'password': password})
    headers = {'Content-Type': 'application/json'}
    return make_request(url, data=data, headers=headers)

def logout_api():
    url = BASE_URL + 'auth/logout'
    return make_request(url)

def check_login_status():
    url = BASE_URL + 'auth/status'
    return make_request(url)

def fetch_account_projects(account_id, number=100, page=0):
    url = BASE_URL + "project/fetch/account/{}?number={}&page={}".format(account_id, number, page)
    return make_request(url)
    
def create_gh_item_list(projects):
    # Get the active document
    doc = Instances.ActiveCanvas.Document
    # Create a new GH_ValueList component
    v = vl()
    # Set the list mode to DropDown
    v.ListMode = Grasshopper.Kernel.Special.GH_ValueListMode.DropDown
    # Clear any existing items in the list
    v.ListItems.Clear()
    # Add items to the value list
    for p in projects:
        v.ListItems.Add(Grasshopper.Kernel.Special.GH_ValueListItem(str(p[0]), str(p[1])))
    # Add the value list component to the document
    doc.AddObject(v, False)
    # Set the output variable
    return True
    

class OpenPlansItem:
    
    def __init__(self, data):
        self.name = data['name']
        self.id = data['id']
        self.architects = data['architects']
        self.civil_engineers = data['civil_engineers']
        self.description = data['description']
        self.year_of_completion = data['year_of_completion']
        self.floor_area = data['floor_area']
        self.floors = data['floors']
        self.geolocation = self.format_geolocation(data['geolocation'])
        self.height = data['height']
        self.projectURL = 'https://plans.arch.ethz.ch/#/project/{}'.format(data['id'])
    
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


class OpenPlansMyProjects(component):

    def RunScript(self, email, password, auth=True):

        if auth is False:
            resp = logout_api()
            if resp['succeeded']:
                return("Logout succeeded"), None
            else:
                ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, resp['error'])
                return(resp['error']), None

        if not email or not password:
            return "Please login with your Open Plans account", None

        user = login(email=email, password=password)


        if user['succeeded']:
            output = ['Login succesfull: \n\n{} \nUser ID = {}'.format(email, user['account_id']), None]
            resp = fetch_account_projects(account_id=user['account_id'])
            if resp['succeeded']:
                project_items = [ OpenPlansItem(p) for p in resp['projects'] ]
                projects = [item.__dict__ for item in project_items]
                output[1] = projects
                #create_gh_item_list( [ (p.name, p.id) for p in project_items ] )
            else:
                ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, resp['error'])
                output[1] = resp['error']
                
            return output[0], output[1]
        else:
            ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, user['error'] + '\nplease check your login credentials')
            return user['error']+ '\nplease check your login credentials', None
