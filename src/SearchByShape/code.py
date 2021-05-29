"""
Retrieve floor plans from the Open Plans database with a geometircal search.
    Inputs:
        SearchShape:    Closed Polyline that represents the desired shape of retrieved floor plans.
                        {item, polyline}
        SearchReload:   (optional: can be None) If True the geometrical search is initiated (again).
                        {item, bool}
        PlanIndex:      Browse the retrieved floor plans (total of 20). Use the plan index
                        to activate one specific floor plan to inspect further.
                        {item, int)
        ImportPlan:     (optional: can be None) Boolean to activate import floor plan into Rhino. If True the floor plan
                        Bitmap and Brep surface are visible in Rhino. 
                        {item, bool}

    Output:
        ImageURL:       URL of the raster image of the retrieved floor plan from Open Plans database
                        {item, string}
        Polygon:        Brep of the retrieved floor plan (section) from Open Plans database
                        {item, Brep}
        BuildingName:   Name of the building floor plan from Open Plans database
                        {item, string}
        BuildingMetrics:Metrics from the retrieved building floor plan from Open Plans database
                        {list, string}
    
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



class SearchByShape(component):
    
    def __init__(self):
        
        self.HERE = ghenv.LocalScope.ghdoc.Path
        self.dir_path = os.path.dirname(self.HERE)
        self.OpenPlansURL = ("https://open-plans.herokuapp.com/searchbyshape")
        self.OpenPlansData = {}
        Rhino.RhinoDoc.AdjustModelUnitSystem(
                       Rhino.RhinoDoc.ActiveDoc, Rhino.UnitSystem.Centimeters, False)
        self.ValidSearchShape = False
        self.SearchShapeIsClosed = False
        self.imageFilePath = self.dir_path + "/" + 'temp_floorplan.jpeg'

    def format_polygon(self, x_coords, y_coords):
        coords = [{'x': x, 'y': y} for x, y in zip(x_coords, y_coords)]
        return {'polygon': coords}

    def getOriginalMetrics(self, json):
        metrics = json['original_metrics']
        metrics = [key + ": " + value for (key, value) in metrics.iteritems()]
        print(metrics)

    def is_shape_valid(self, shape):
        if shape.IsValid is False:
            print("invalid search shape")
            self.ValidSearchShape = False
        else:
            self.ValidSearchShape = True

    def is_shape_closed(self, shape):

        if shape.IsClosed:
            print("valid search shape")
            self.SearchShapeIsClosed = True
        else:
            print('polygon is not closed')
            self.SearchShapeIsClosed = False

    def shape_coordinates(self, shape):
        x_coords = [x for x in shape.X]
        # flip y coordinate to start top left as 0, 0 (image coordinate system)
        y_coords = [y*-1 for y in shape.Y]
        polygon = self.format_polygon(x_coords, y_coords)
        return json.dumps(polygon)

    def retrieve_image_url(self, json, index):
        """
        Get all url's to retrieve floorplan images from the server
        Returns url of input index plan
        """
        if 'image_paths' not in self.OpenPlansData:
            self.OpenPlansData['image_paths'] = [p['image_path']
                                            for p in json['similar_plan_list']]
        return self.OpenPlansData['image_paths'][index]


    def retrieve_polygon(self, json, index):
        """
        Get all polygon coordinates from the json response and create a boundary surface
        Returns the polygon of input index
        """
        if 'polylines' not in self.OpenPlansData:
            polygon_coords = [p['points'] for p in json['similar_plan_list']]
            polygon_coords = [map(self.transform_to_rhino_coords, c)
                            for c in polygon_coords]
            polylines = []
            for polygon in polygon_coords:
                polyline = rg.Polyline()
                for pt in polygon:
                    polyline.Add(rg.Point3d(pt[0], pt[1], 0))
                polylines.append(polyline)
            self.OpenPlansData['polylines'] = polylines
        polyline = self.OpenPlansData['polylines'][index]
        polygon = rg.Brep()
        polylineCrv = polyline.ToPolylineCurve()
        polygon = polygon.CreatePlanarBreps(polylineCrv)[0]
        polygon.Scale(0.1)
        return polygon


    def transform_to_rhino_coords(self, coordinate):
        """ 
        Flip y coordinate to match Rhino system
        Starting top left as 0, 0

        Returns : [ x, y ] 
        """
        return list([coordinate[0], coordinate[1]*-1])


    def retrieve_building_names(self, json, index):
        """
        Get all building names from similar buildings
        Returns building name of input index
        """
        if 'names' not in self.OpenPlansData:
            self.OpenPlansData['names'] = [p['name']
                                    for p in json['similar_plan_list']]
        return self.OpenPlansData['names'][index]


    def getTransform(self, plane, scale):
        """
        Transforms plane by moving it down to match top left coordinate with Rhino 0, 0 (x, y) position
        """
        width, height, mms_pp = scale[0], scale[1], scale[2]

        # move plane down along vector
        plane.Translate(rg.Vector3d(0, -height/mms_pp, 0))


    def getScale(self, json, index):
        """
        Get scale metrics from all floorplan images
        Returns scale metrics of input index
        """
        if 'scale' not in self.OpenPlansData:
            self.OpenPlansData['scale'] = [
                (p['width_mm'], p['height_mm'], p['mms_per_pixel']) for p in json['similar_plan_list']]
        return self.OpenPlansData['scale'][index]


    def getMetrics(self, json, index):
        """
        Print all metrics from the similar polygon
        """
        if 'metrics' not in self.OpenPlansData:
            self.OpenPlansData['metrics'] = [p['metrics']
                                        for p in json['similar_plan_list']]

        metrics = [key + ": " + value for (key, value)
                in self.OpenPlansData['metrics'][index].iteritems()]
        return metrics


    def import_plan2rhino(self, img_url, scale):
        """
        This function loads the floorplan image from the server through the input url.
        And sets the image as a background bitmap in Rhino
        """

        # read url
        response = urllib2.urlopen(img_url)
        output = open(self.imageFilePath, "wb")
        output.write(response.read())
        output.close()

        # Rhino Bitmap
        bitmap = rd.DisplayBitmap.Load(img_url)

        # get active view
        view = scriptcontext.doc.Views.ActiveView
        plane = view.ActiveViewport.ConstructionPlane()
        # transform plane to flip image coordinate system
        self.getTransform(plane, scale)
        # load image into Rhino view
        view.ActiveViewport.SetTraceImage(
            self.imageFilePath, plane, bitmap.Size.Width, bitmap.Size.Height, True, False)
        view.Redraw()


    def RunScript(self, SearchShape, SearchReload, PlanIndex, ImportPlan=True):

        self.is_shape_valid(SearchShape)
        self.is_shape_closed(SearchShape)

        req = urllib2.Request(self.OpenPlansURL, self.shape_coordinates(SearchShape), headers={'Content-Type': 'application/json'})
        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            print(e)

        resp = response.read()

        # from string to JSON
        self.OpenPlansData['response'] = json.loads(resp)

        # print input search shape metrics
        self.getOriginalMetrics(self.OpenPlansData['response'])

        ImageURL = self.retrieve_image_url(self.OpenPlansData['response'], PlanIndex)
        BuildingName = self.retrieve_building_names(self.OpenPlansData['response'], PlanIndex)
        BuildingMetrics = self.getMetrics(self.OpenPlansData['response'], PlanIndex)


        if ImportPlan is False:
            scriptcontext.doc.Views.ActiveView.ActiveViewport.ClearTraceImage()
            try:
                os.remove(self.imageFilePath)
            except OSError, e:
                print(e)
        else:
            scale = self.getScale(self.OpenPlansData['response'], PlanIndex)
            self.import_plan2rhino(ImageURL, scale)
            Polygon = self.retrieve_polygon(self.OpenPlansData['response'], PlanIndex)
        
        return ImageURL, Polygon, BuildingName, BuildingMetrics
#
#sbs = SearchByShape()
#image_url, building_name, building_metrics, polygon = sbs.RunScript(SearchShape, SearchReload, PlanIndex, ImportPlan)