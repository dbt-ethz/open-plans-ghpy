"""
    Remarks:
        Author: 
        License:
        Version: 
"""
import copy

from ghpythonlib.componentbase import executingcomponent as component


POLYGON_FIELDS = {
    "id": None,
    "plan_id": None,
    "points": [],
    "tags": []
}


class OpenPlansPolygonObj:

    def __init__(self, data_fields=None):
        if data_fields is None:
            data_fields = copy.deepcopy(POLYGON_FIELDS)
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
        return cls(data_fields={k: v for k, v in data.iteritems() if k in POLYGON_FIELDS})

    @classmethod
    def from_polygon_id(cls, id):
        pass

    @property
    def polygon(self):
        return self.__polygon

    @property
    def polygon_id(self):
        return self.polygon['id']

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

    def clear_tags(self):
        self.__polygon['tags'] = []
    
    def rhino_curve_to_data_points(self, obj, move_y=None):
        """Set Rhino document user text.

        Parameters
        ----------
        obj : polyline
            rhino geometry polyline

        Returns
        -------
        points data: dict
            the points from polygon in dict format of open plans
        """
        if obj:
            points = [ p for p in obj ]
        if move_y:
            pts_data = [{'x': p.X, 'y': (p.Y - move_y) * -1} for p in points]
            self.__polygon['points'] = pts_data
        else:
            pts_data = [{'x': p.X, 'y': p.Y} for p in points]
            self.__polygon['points'] = pts_data
        
    def move_data_pts_to_positive(self, move_y):
        pts = [{'x': p['x'], 'y': (p['y'] - move_y) * -1} for p in self.points]
        self.__polygon['points'] = pts


class OpenPlansImport(component):

    def RunScript(self, polyline, tags):
        
        OpenPlansPolygon = []
        
        for p in polyline:
            if p:
                polygon = OpenPlansPolygonObj()
                
                polygon.rhino_curve_to_data_points(obj=p)
    
                if tags:
                    polygon.clear_tags()
                    for tag in tags:
                        polygon.add_polygon_tag(tag=tag)
                        
                OpenPlansPolygon.append(polygon)

        return OpenPlansPolygon
