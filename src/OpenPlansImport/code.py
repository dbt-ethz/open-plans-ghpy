"""
    Remarks:
        Author: 
        License:
        Version: 
"""
import urllib2
from urllib2 import HTTPError, URLError
import json
import copy
import tempfile
import os

from ghpythonlib.componentbase import executingcomponent as component
import Rhino.Display as rd
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext
from System.Drawing import Color
import Grasshopper.Kernel as gh

scriptcontext.doc = Rhino.RhinoDoc.ActiveDoc

BASE_URL = "https://open-plans.herokuapp.com/"

PROJECT_FIELDS = {
    "id": None,
    "name": "",
    "description": "",
    "civil_engineers": "",
    "architects": "",
    "source": "",
    "year_of_completion": None,
    "clients": "",
    "floors": None,
    "height": None,
    "floor_area": None,
    "plans": [],
    "tags": [],
    "latitude": None,
    "longitude": None
}

PLAN_FIELDS = {
    "id": None,
    "image_path": "",
    "image_data": "",
    "mms_per_pixel": None,
    "width_mm": None,
    "height_mm": None,
    "type": None,
    "orientation": None,
    "floor": None,
    "source": "",
    "polygons": [],
    "project_id": None
}

POLYGON_FIELDS = {
    "id": None,
    "plan_id": None,
    "points": [],
    "tags": []
}

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
    
def fetch_project(project_id):
    url = BASE_URL + 'project/fetch/{}'.format(project_id)
    return make_request(url)

def add_parent_layer(lname, attr=None):
    if not rs.IsLayer(lname):
        lname = rs.AddLayer(name=lname, color=None,
                            visible=True, locked=False, parent=None)
        rs.CurrentLayer(lname)

    layer_id = rs.LayerId(lname)

    return lname, layer_id

def add_child_layer(lname, parent, attr=None):
    # Add layer if it does not exist yet
    if not (rs.IsLayer(lname) and rs.IsLayerParentOf(lname, parent)):
        lname = rs.AddLayer(name=lname, color=None,
                            visible=True, locked=False, parent=parent)
        layer_id = rs.LayerId(lname)
        # move layer under parent layer
        rs.ParentLayer(layer=lname, parent=parent)
        # fullpath layername
        lname = rs.LayerName(layer_id=layer_id, fullpath=True)
    else:
        layer_id = rs.LayerId("{}::{}".format(parent, lname))
        lname = rs.LayerName(layer_id)


    return lname, layer_id

def project_to_rhino_layers(plan, plan_id=None):
    """Add Project instance to Rhino document layers.

    Parameters
    ----------
    project : :class: 'OpenPlansProject'
        open plans project instance.

    Returns
    -------

    """
    # plan layer
    project_lname, project_lid = add_child_layer(
        lname=plan.plan_id_string, parent=add_parent_layer('OpenPlans')[0])

    if plan_id:
    # polygon layers
        _polygon_layers = add_polygon_rhino_layers(plan)

def polygon_to_rhino_layer(polygon, layer):
    """Add Polygon instance to Rhino document layer.

    Parameters
    ----------
    geom : :class: 'Polygon'
        Polygon instance.
    layer : str
        Rhino.Layer name
    attr : dict
        if dict, key value pairs of object's attributes
        are stored in Rhino Object User text

    Returns
    -------

    """
    obj = rs.AddPolyline(polygon.points)
    rs.ObjectLayer(object_id=obj, layer=layer)

def add_polygon_rhino_layers(plan):
    """Add Rhino Layers and Rhino.Polylines 
    from Plan instance Polygons.

    Parameters
    ----------
    plan : :class: 'OpenPlansPlan'
        open plans plan instance.

    Returns
    -------
    polygon_layers : list[str]
        list of layer names from polygon layers
    """
    p_layers = []
    for polygon in plan.plan_polygon_objs():
        polygon_tags_str = ', '.join(map(str, polygon.tags)) if polygon.tags else "None"
        lname, lid = add_child_layer(lname='{} ({})'.format(polygon_tags_str, plan.plan_id_string.split(' ')[0]), parent=rs.LayerName(plan.plan_id_string, fullpath=True))
        rs.LayerColor(lname, Color.FromArgb(0, 0, 255))
        p_layers.append(lname)
        # add geometry to layer
        polygon_to_rhino_layer(
            polygon=polygon.rhino_polygon(frame_height=plan.height_mm), layer=lname)

    return p_layers


class OpenPlansPlanObj:

    def __init__(self, data_fields=None):
        if data_fields is None:
            data_fields = copy.deepcopy(PLAN_FIELDS)
        self.__plan = data_fields

    @classmethod
    def from_data(cls, data):
        """Construct a Open Plans plan from its api data representation.

        Parameters
        ----------
        data : dict
            The data dictionary.

        Returns
        -------
        :class:`OpenPlansPlan`
            The constructed dataclass.
        """
        return cls(data_fields={k: v for k, v in data.iteritems() if k in PLAN_FIELDS})

    @classmethod
    def from_plan_id(cls, id):
        return cls.from_data(data=get_data(dict=fetch_plan(plan_id=id), key='plan'))

    @property
    def plan(self):
        return self.__plan

    @property
    def plan_id(self):
        return self.plan['id']
    
    @property
    def project_id(self):
        return self.plan['project_id']

    @property
    def floor(self):
        return self.plan['floor']

    @property
    def polygons(self):
        try:
            return self.plan['polygons']
        except:
            self.__plan['polygons'] = []
            return self.plan['polygons']

    @property
    def image_path(self):
        return self.plan['image_path']

    @property
    def mms_per_pixel(self):
        return self.plan['mms_per_pixel']

    @property
    def height_mm(self):
        return self.plan['height_mm']

    @property
    def width_mm(self):
        return self.plan['width_mm']

    @property
    def plan_id_string(self):
        return "{} Level; ID: {}".format(str(self.floor).zfill(2), self.plan_id)

    @property
    def attributes(self):
        return {k: v for k, v in self.plan.iteritems() if k not in ['polygons']}

    def get_project_id(self):
        return get_data(dict=fetch_plan(plan_id=self.plan_id), key='plan')['project_id']

    def plan_polygon_objs(self):
        return [OpenPlansPolygon.from_data(data=poly)
                for poly in self.plan['polygons']]

    def add_polygon(self, polygon):
        if type(polygon) is dict:
            data = polygon.copy()
            self.__plan['polygons'].append(data)
        else:
            ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, "No polygons have been added to the plan")
        return self

    def remove_empty_values(self, data=None):

        data = self.plan if not data else data

        cleaned_dict = {}
        for key, value in data.iteritems():
            if type(value) is list:
                nested_dicts = [self.remove_empty_values(data=x) for x in value if type(
                    x) is dict and self.remove_empty_values(data=x)]

                cleaned_dict[key] = nested_dicts if len(
                    nested_dicts) > 0 else value if len(value) > 0 else []

            elif value:
                cleaned_dict[key] = value

        return cleaned_dict
    
    def clear_polygons(self):
        self.__plan['polygons'] = []
    
    def draw_image_plan(self):

        def read_image_url(img_url):
            response = urllib2.urlopen(img_url)
            return response.read()
        # try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpeg")
        temp_file.write(read_image_url(self.image_path))
        temp_file.close()
            
        RhinoDocument = Rhino.RhinoDoc.ActiveDoc
        view = RhinoDocument.Views.Find("Top", False)

        plane = view.ActiveViewport.ConstructionPlane()

        # load image into Rhino view
        view.ActiveViewport.SetTraceImage(
            temp_file.name, plane, self.width_mm, self.height_mm, True, False)
        view.Redraw()

        os.remove(temp_file.name)

        # except:
        #     ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, 
        #                                       'Image cannot be displayed')
            

class Polygon:

    def __init__(self, points=None, move_y=0):
        self.__points = points
        self.__frame_h = move_y

    @property
    def points(self):
        return self.__points

    @classmethod
    def from_data(cls, data, move_y=0):
        return cls(points=[[p['x'], p['y']*-1 + move_y]
                           for p in data])



class OpenPlansImport(component):

    def RunScript(self, planID, importToRhino):
        
        plan = None
        
        if planID:
            plan = OpenPlansPlanObj.from_plan_id(id=planID)
        
        if plan:
            if importToRhino:
                plan.draw_image_plan()
                # if plan.polygons:
                #     project_to_rhino_layers(plan=plan, plan_id=planID)

        return plan
