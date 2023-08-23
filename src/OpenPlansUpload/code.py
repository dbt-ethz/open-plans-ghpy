"""
    Remarks:
        Author: 
        License:
        Version: 
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
import urllib2
from urllib2 import HTTPError
import json
import copy

from ghpythonlib.componentbase import executingcomponent as component
import Rhino.Geometry as rg
import ghpythonlib.treehelpers as th
import rhino.geometry
import rhino.rhino_helpers


URI = "https://open-plans.herokuapp.com/"

project_fields = {
    "project_id": None,
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

plan_fields = {
    "plan_id": None,
    "image_path": "",
    "image_data": "",
    "mms_per_pixel": None,
    "width_mm": None,
    "height_mm": None,
    "type": None,
    "orientation": None,
    "floor": None,
    "source": "",
    "polygons": []
}

polygon_fields = {
    "polygon_id": None,
    "plan_id": None,
    "points": [],
    "tags": []
}

def save_project(project):
    url = URI + 'project/save'
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
        print(e)
        raise

def fetch_project(project_id):
    url = URI + 'project/fetch/{}'.format(project_id)
    req = urllib2.Request(url)

    try:
        response = urllib2.urlopen(req)
        json_string = response.read().decode('utf-8')
        retVal = dict(json.loads(json_string))
        return retVal
    except HTTPError as e:
        print(e)

def check_login_status():
    url = URI + 'auth/status'
    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req)
        json_string = response.read().decode('utf-8')
        retVal = dict(json.loads(json_string))
        return retVal
    except HTTPError as e:
        return {"succeeded": 0, "error": e}

def fetch_plan(plan_id):
    url = URI + 'plan/fetch/{}'.format(plan_id)
    req = urllib2.Request(url)

    try:
        response = urllib2.urlopen(req)
        json_string = response.read().decode('utf-8')
        retVal = dict(json.loads(json_string))
        return retVal  
    except HTTPError as e:
        return {"succeeded": 0, "error": e}
    
def get_data(dict, key):
    if dict['succeeded']:
        return dict[key]
    else:
        try:
            print(dict['error'])
        except:
            print('failed without error message')



class OpenPlansProject:

    def __init__(self, data_fields=copy.deepcopy(project_fields)):
        self.__project = data_fields

    @classmethod
    def from_data(cls, data):
        """Construct a Open Plans Project from its api data representation.

        Parameters
        ----------
        data : dict
            The data dictionary.

        Returns
        -------
        :class:`OpenPlansProject`
            The constructed dataclass.
        """
        
        return cls(data_fields={k: v for k, v in data.iteritems() if k in project_fields})

    @classmethod
    def from_custom(cls, data=None, **kwargs):
        project_attr = copy.deepcopy(project_fields)
        if data:
            
            for key in data:
                if data[key]:
                    project_attr[key] = data[key]

        for key in kwargs:
            project_attr[key] = kwargs[key]

        return cls(data_fields=project_attr)

    @classmethod
    def from_project_id(cls, id):
        return cls.from_data(data=get_data(dict=fetch_project(project_id=id), key='project'))

    @property
    def project(self):
        return self.__project

    @property
    def plans(self):
        return self.project['plans']

    @property
    def name(self):
        return self.project['name']

    @property
    def project_id(self):
        return self.project['project_id']

    @property
    def plan_ids(self):
        return [p['id'] for p in self.plans if p['id']]

    @property
    def attributes(self):
        return {k: v for k, v in self.project.iteritems() if k not in ['plans']}

    def add_plan(self, plan):
        if isinstance(plan, OpenPlansPlan):
            self.__project['plans'].append(plan.plan)
        elif type(plan) is dict:
            self.__project['plans'].append(plan)
        return self

    def plan_objs(self):
        return [OpenPlansPlan.from_custom(data=plan) for plan in self.plans]

    def get_plan_objs_from_ids(self, plan_ids=None):
        """Constructs OpenPlansPlan object instances from plan data.

        Parameters
        ----------
        [Optional] plan_ids : list
            If ids of plans given, only selected plans will be returned.

        Returns
        -------
        list[:class:`OpenPlansProject`]
            List of the constructed class instances.
        """
        if plan_ids:
            return [OpenPlansPlan.from_data(p) for p in self.plans if p['id'] in plan_ids]
        else:
            return [OpenPlansPlan.from_data(p) for p in self.plans]

    def modify_project(self, field_changes={}, **kwargs):
        for key in field_changes:
            self.__project[key] = field_changes[key]
        for key in kwargs:
            self.__project[key] = kwargs[key]
        return self

    def fetch_project_plans(self, plan_ids=None):
        if plan_ids:
            return [OpenPlansPlan.from_plan_id(id=id) for id in plan_ids]
        else:
            return [OpenPlansPlan.from_plan_id(id=id) for id in self.plan_ids]

    @property
    def project_id_string(self):
        return "Name: {}; ID: {}".format(
            self.name, self.project_id)

    def __repr__(self):
        return "{}(project={})".format(self.__class__.__name__, self.project)

    def remove_empty_values(self, data=None):
        """Remove empty values from dictionary, except for empty lists.

        Parameters
        ----------
        [Optional] data : dict
            if given, the data dictionary to remove empty values from, 
            else it takes the project dictionary.

        Returns
        -------
        cleaned_dict : dict
            The cleaned dictionary without empty values.
        """
        data = self.project if not data else data
        cleaned_dict = {}
        for key, value in data.iteritems():
            if type(value) is list:
                nested_dicts = [self.remove_empty_values(data=x) for x in value if type(
                    x) is dict and self.remove_empty_values(data=x)]

                cleaned_dict[key] = nested_dicts if len(
                    nested_dicts) > 0 else value if len(value) > 0 else []
            elif value:
                cleaned_dict[key] = value
            
            elif key == 'image_path' or key == 'image_data':
                cleaned_dict[key] = value

        return cleaned_dict

    def format_geolocation(self, data=None):
        data = self.project if not data else data
        lat = data.pop('latitude')
        long = data.pop('longitude')
        data['geolocation'] = {'longitude': long, 'latitude': lat}
        return data

    def upload_to_openplans(self):
        """Upload the project dictionary to the Open Plans database
        through a REST api request (post).

        Returns
        -------
        : str
            Project id if succesful, else error message
        """
        upload_data = self.remove_empty_values()
        #upload_data = self.project
        resp = save_project(upload_data)
        if resp['succeeded']:
            print('Project succesfully uploaded to Open Plans; Project(id={})'.format(
                resp['project_id']))
        else:
            print(resp['error'])


class OpenPlansPlan:

    def __init__(self, data_fields=copy.deepcopy(plan_fields)):
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
        if 'id' in data.keys():
            data['plan_id'] = data.pop('id')
        return cls(data_fields={k: v for k, v in data.iteritems() if k in plan_fields})

    @classmethod
    def from_custom(cls, data=None, **kwargs):
        plan_attr = copy.deepcopy(plan_fields)
        if data:
            if 'id' in data.keys():
                data['plan_id'] = data.pop('id')
            for key in data:
                plan_attr[key] = data[key]
        for key in kwargs:
            plan_attr[key] = kwargs[key]
        return cls(data_fields=plan_attr)

    @classmethod
    def from_plan_id(cls, id):
        return cls.from_data(data=get_data(dict=fetch_plan(plan_id=id), key='plan'))

    @property
    def plan(self):
        return self.__plan

    @property
    def plan_id(self):
        return self.plan['plan_id']

    @property
    def floor(self):
        return self.plan['floor']

    @property
    def polygons(self):
        data = self.plan['polygons']
        polygons = []
        for p in data:
            if 'id' in p.keys():
                p['polygon_id'] = p.pop('id')
            polygons.append(p)
        return polygons

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

    def set_image_size(self, frame_size, mms_per_pixel=10):
        self.__plan["width_mm"], self.__plan["height_mm"] = frame_size[0], frame_size[1]
        self.__plan['mms_per_pixel'] = mms_per_pixel
        return self

    def plan_polygon_objs(self):
        return [OpenPlansPolygon.from_data(data=poly)
                for poly in self.plan['polygons']]

    def add_polygon(self, polygon):
        if isinstance(polygon, OpenPlansPolygon):
            self.plan['polygons'].append(polygon.polygon)
        elif type(polygon) is dict:
            self.plan['polygons'].append(polygon)
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


class OpenPlansPolygon:

    def __init__(self, data_fields=copy.deepcopy(polygon_fields)):
        self.__polygon = data_fields

    @classmethod
    def from_data(cls, data):
        """Construct a Open Plans polygon from its api data representation.

        Parameters
        ----------
        data : dict
            The data dictionary.

        Returns
        -------
        :class:`OpenPlansPolygon`
            The constructed dataclass.
        """
        if 'id' in data.keys():
            data['polygon_id'] = data.pop('id')
        return cls(data_fields={k: v for k, v in data.iteritems() if k in polygon_fields})

    @classmethod
    def from_custom(cls, data=None, **kwargs):
        polygon_attr = copy.deepcopy(polygon_fields)
        if data:
            if 'id' in data.keys():
                data['polygon_id'] = data.pop('id')
            for key in data:
                if data[key]:
                    polygon_attr[key] = data[key]

        for key in kwargs:
            polygon_attr[key] = kwargs[key]
        return cls(data_fields=polygon_attr)

    @classmethod
    def from_polygon_id(cls, id):
        pass

    @classmethod
    def from_rhino_object(cls, rhobj, frame_size=None):
        data = rhino.rhino_helpers.get_object_user_text(object_id=rhobj)
        data['points'] = rhino.rhino_helpers.rhino_curve_to_data_points(
            rhobj, frame_size)
        return cls.from_custom(data=data)

    @property
    def polygon(self):
        return self.__polygon

    @property
    def polygon_id(self):
        return self.polygon['polygon_id']

    @property
    def plan_id(self):
        return self.polygon['plan_id']

    @property
    def tags(self):
        return self.polygon['tags']

    @property
    def points(self):
        return self.polygon['points']

    @property
    def polygon_id_string(self):
        return "tags: {}; ID: {}".format(self.tags, self.polygon_id)

    @property
    def attributes(self):
        return {k: v for k, v in self.polygon.iteritems() if k not in ['points']}

    def add_polygon_tag(self, tag):
        self.__polygon['tags'].append(tag)

    def rhino_polygon(self, frame_height=0):
        return rhino.geometry.Polygon.from_data(data=self.points, move_y=frame_height)

    def remove_empty_values(self):
        return {k: v for k, v in self.polygon.iteritems() if v}

    def transform_rhino_to_image_coordinates(self, frame_size):
        pass


class OpenPlansUpload(component):

    def RunScript(self, project):

        user = check_login_status()
        if user['is_logged']:
            return "logged in"

