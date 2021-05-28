from ghpythonlib.componentbase import executingcomponent as component
import urllib2
import json
import Rhino
import Rhino.Geometry as rg
import Rhino.Display as rd
import scriptcontext
from ghpythonlib.components import BoundarySurfaces
import os


HERE = ghenv.LocalScope.ghdoc.Path
dir_path = os.path.dirname(HERE)

# Set unit system to centimeters
Rhino.RhinoDoc.AdjustModelUnitSystem(Rhino.RhinoDoc.ActiveDoc,Rhino.UnitSystem.Centimeters, False)

openplans_data = {}

if search_reload:
    openplans_data = {}
    

def format_polygon(x_coords, y_coords):
    coords = [ {'x' : x, 'y' : y} for x, y in zip(x_coords, y_coords) ]
    return {'polygon' : coords }
    
def getOriginalMetrics(json):
    metrics = json['original_metrics']
    metrics = [ key + ": " + value for (key, value) in metrics.iteritems() ]
    print(metrics)
    
if search_shape.IsValid is False:
    print("invalid search shape")

if search_shape.IsClosed:
    print("valid search shape")
    x_coords = [ x for x in search_shape.X ]
    y_coords = [ y*-1 for y in search_shape.Y ] # flip y coordinate to start top left as 0, 0 (image coordinate system)
    polygon = format_polygon(x_coords, y_coords)
    data = json.dumps(polygon)
else:
    print('polygon is not closed')
    
# Query URL
url = ("https://open-plans.herokuapp.com/searchbyshape")

req = urllib2.Request(url, data, headers={'Content-Type': 'application/json'})
try:
    response = urllib2.urlopen(req)
except urllib2.HTTPError, e:
    print(e)

resp = response.read()

# from string to JSON
plans_response = json.loads(resp)

# print input search shape metrics
getOriginalMetrics(plans_response)

openplans_data['response'] = plans_response


def retrieve_image_url(json, index):
    """
    Get all url's to retrieve floorplan images from the server
    Returns url of input index plan
    """
    if 'image_paths' not in openplans_data:
        openplans_data['image_paths'] = [ p['image_path'] for p in json['similar_plan_list'] ]
    return openplans_data['image_paths'][index]
    
def retrieve_polygon(json, index):
    """
    Get all polygon coordinates from the json response and create a boundary surface
    Returns the polygon of input index
    """
    if 'polylines' not in openplans_data:
        polygon_coords = [p['points'] for p in json['similar_plan_list'] ]
        polygon_coords = [ map(transform_to_rhino_coords, c)  for c in polygon_coords ]
        polylines = []
        for polygon in polygon_coords:
            polyline = rg.Polyline()
            for pt in polygon:
                polyline.Add(rg.Point3d(pt[0], pt[1], 0))
            polylines.append(polyline)
        openplans_data['polylines'] = polylines
    polyline = openplans_data['polylines'][index]
    polygon = rg.Brep()
    polylineCrv = polyline.ToPolylineCurve()
    polygon = polygon.CreatePlanarBreps(polylineCrv)[0]
    polygon.Scale(0.1)
    return polygon
    
def transform_to_rhino_coords(coordinate):
    """ 
    Flip y coordinate to match Rhino system
    Starting top left as 0, 0
    
    Returns : [ x, y ] 
    """
    return list([coordinate[0], coordinate[1]*-1])
    
def retrieve_building_names(json, index):
    """
    Get all building names from similar buildings
    Returns building name of input index
    """
    if 'names' not in openplans_data:
        openplans_data['names'] = [p['name'] for p in json['similar_plan_list'] ]
    return openplans_data['names'][index]
    
def getTransform(plane):
    """
    Transforms plane by moving it down to match top left coordinate with Rhino 0, 0 (x, y) position
    """
    scale = getScale()
    width, height, mms_pp = scale[0], scale[1], scale[2]

    # move plane down along vector
    plane.Translate(rg.Vector3d(0, -height/mms_pp, 0))
    
def getScale(json=plans_response, index=plan_idx):
    """
    Get scale metrics from all floorplan images
    Returns scale metrics of input index
    """
    if 'scale' not in openplans_data:
        openplans_data['scale'] = [ (p['width_mm'], p['height_mm'], p['mms_per_pixel']) for p in json['similar_plan_list'] ]
    return openplans_data['scale'][index]
    
def getMetrics(json, index):
    """
    Print all metrics from the similar polygon
    """
    if 'metrics' not in openplans_data:
        openplans_data['metrics'] = [p['metrics'] for p in json['similar_plan_list'] ]

    metrics = [ key + ": " + value for (key, value) in openplans_data['metrics'][index].iteritems() ]
    return metrics
    
def import_plan2rhino(url):
    """
    This function loads the floorplan image from the server through the input url.
    And sets the image as a background bitmap in Rhino
    """
    
    # read url
    response = urllib2.urlopen(url)
    output = open(filePath, "wb")
    output.write(response.read())
    output.close()
    
    # Rhino Bitmap
    bitmap = rd.DisplayBitmap.Load(url)
    
    # get active view
    view = scriptcontext.doc.Views.ActiveView
    plane = view.ActiveViewport.ConstructionPlane()
    # transform plane to flip image coordinate system
    getTransform(plane) 
    # load image into Rhino view
    view.ActiveViewport.SetTraceImage(filePath, plane, bitmap.Size.Width, bitmap.Size.Height, True, False)
    view.Redraw()



image_url = retrieve_image_url(plans_response, plan_idx)
building_name = retrieve_building_names(plans_response, plan_idx)
building_metrics = getMetrics = getMetrics(plans_response, plan_idx)

filename = 'temp_floorplan.jpeg'
filePath = dir_path + "/" + filename

if import_plan is False:
    scriptcontext.doc.Views.ActiveView.ActiveViewport.ClearTraceImage()
    try:
        os.remove(filePath)
    except OSError, e:
        print(e)
else:  
    import_plan2rhino(image_url)
    polygon = retrieve_polygon(plans_response, plan_idx)