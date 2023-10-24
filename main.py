import json
import math
import requests
from bs4 import BeautifulSoup

EPSILON = 0.01
BASE_URL = "https://www.airnav.com/airport/"


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Line:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2


### Return an array of booleans corresponding to whether or not each airport is within the polygon
def airportsInPolygon(airports, polygon, sorted=True):
    poly_sides = len(polygon)

    # if polygon has fewer than 3 sides, not possible for point to be inside
    if poly_sides < 3:
        print("Error: polygon must have at least 3 sides")
        return [False]*len(airports)
    
    # Sort polygon clockwise if not sorted clockwise
    if not sorted:
        polygon = sortPoly(polygon)

    f = open('airport_coords.json')
    airport_coords = json.load(f)
    f.close()

    x_coords = [x[0] for x in polygon]
    xMin = min(x_coords)
    xMax = max(x_coords)

    y_coords = [x[1] for x in polygon]
    yMin = min(y_coords)
    yMax = max(y_coords)

    # Point guaranteed to be outside polygon
    outerPoint = Point(xMin - 10, yMin - 10)

    ans = []
    for a in airports:
        if a in airport_coords:
            coord = [float(x) for x in airport_coords[a].split(",")]
        elif "K" + a in airport_coords:
            coord = [float(x) for x in airport_coords["K" + a].split(",")]
        else: # (unlikely) case that airport missing from JSON file
            # Try to scrape
            page = requests.get(BASE_URL + a)
            if not page.ok:
                print("Error:", a, "is an invalid FAA ID")
                ans.append(False) # could not access airport coordinates
                continue

            soup = BeautifulSoup(page.content, "html.parser")
            coordSoup = soup.find_all("td", string="Lat/Long: ")
            if len(coordSoup) == 0: # accessed invalid page without latitude/longitude coordinates
                print("Error:", a, "is an invalid FAA ID")
                ans.append(False) 
                continue
            
            coordStr = coordSoup[0].find_next_sibling("td").find_all("br")[-2].nextSibling
            coord = [float(x) for x in coordStr.split(",")]

        airport = Point(coord[0], coord[1])

        # if airport outside min/max bounds, then definitely not in polygon
        if airport.x < xMin or airport.x > xMax or airport.y < yMin or airport.y > yMax:
            ans.append(False)
            continue

        # line from outside the polygon to aiport
        airportLine = Line(outerPoint, airport)
        
        intersections = 0
        for i in range(poly_sides):
            sidePt1 = Point(polygon[i % poly_sides][0], polygon[i % poly_sides][1])
            sidePt2 = Point(polygon[(i + 1) % poly_sides][0], polygon[(i + 1) % poly_sides][1])
            side = Line(sidePt1, sidePt2)
            if intersection(side, airportLine):
                intersections += 1

        if intersections % 2 == 1:
            ans.append(True) # airport is inside polygon if odd number of intersections
        else:
            ans.append(False) # airport is outside polygon if even number intersections
    
    return ans


### Sort the points of a polygon clockwise; note polygon must be convex
def sortPoly(polygon):
    n = len(polygon)

    # Get center point
    x = [p[0] for p in polygon]
    y = [p[1] for p in polygon]
    center = (sum(x) / n, sum(y) / n)

    # Get radians of point from center
    degreePoints = []
    for point in polygon:
        dx = point[0] - center[0] # Difference in x coordinates
        dy = point[1] - center[1] # Difference in y coordinates
        theta = math.atan2(dy, dx) # Angle between point and center in radians
        degreePoints.append((theta, point))

    # Sort by radians
    degreePoints.sort(key=lambda x:x[0])

    # Return just the lat/long points
    return [x[1] for x in degreePoints]


### Check whether two lines intersect
def intersection(line1, line2):
    dir1 = rotation(line1.p1, line1.p2, line2.p1)
    dir2 = rotation(line1.p1, line1.p2, line2.p2)
    dir3 = rotation(line2.p1, line2.p2, line1.p1)
    dir4 = rotation(line2.p1, line2.p2, line1.p2)

    # Intersection
    if dir1 != dir2 and dir3 != dir4:
        return True
 
    ### In the case that the points are colinear, we check if there is intersection
    # Colinear and p1 of line2 is on line1
    if dir1 == 0 and onLine(line1, line2.p1):
        return True
 
    # Colinear and p2 of line2 is on line1
    if dir2 == 0 and onLine(line1, line2.p2):
        return True
 
    # Colinear and p1 of line1 is on the line2
    if dir3 == 0 and onLine(line2, line1.p1):
        return True
 
    # Colinear and p2 of line1 is on the line2
    if dir4 == 0 and onLine(line2, line1.p2):
        return True

    return False


### Find the orientation of the ordered points
def rotation(p1, p2, p3):
    test = (p2.y - p1.y) * (p3.x - p2.x) - (p2.x - p1.x) * (p3.y - p2.y)
    if -1 * EPSILON < test < EPSILON: # use EPSILON due as buffer for floating point inaccuracies
        # Colinear
        return 0
    elif test < 0:
        # Anti-clockwise
        return 2
    else:
        # Clockwise
        return 1

### Check whether a point is on a line
def onLine(line, point):
    if (
        point.x <= max(line.p1.x, line.p2.x)
        and point.x >= min(line.p1.x, line.p2.x)
        and (point.y <= max(line.p1.y, line.p2.y)and point.y >= min(line.p1.y, line.p2.y))
    ):
        return True
    return False


### TEST CASES ###
# New York 1
print("New York 1")
airports_1 = ['JFK', 'LGA', 'EWR', 'HPN']
polygon_1 = [[40.01737, -76.02493], [39.96693, -71.78971], [41.87763, -73.97102]]
res_1 = airportsInPolygon(airports_1, polygon_1)
expected_1 = [True, True, True, True]
print("Result:", res_1)
print("Expected:", expected_1)
print("Passed:", res_1 == expected_1, "\n")

# New York 2
print("New York 2")
airports_2 = ['JFK', 'LGA', 'EWR', 'HPN']
polygon_2 = [[40.54757, -74.3368], [40.36164, -73.94541], [40.58513, -73.49088], [40.88782, -73.6639], [40.8172, -74.19124]]
res_2 = airportsInPolygon(airports_2, polygon_2)
expected_2 = [True, True, True, False]
print("Result:", res_2)
print("Expected:", expected_2)
print("Passed:", res_2 == expected_2, "\n")

# Montana
print("Montana")
airports_3 = ['MSO', 'GTF', 'BZN', 'BIL', 'HLN', 'SDY', 'GPI', 'BTM', 'WYS']
polygon_3 = [[44.48065, -111.32685], [45.20365, -109.65164], [47.61259, -110.49757], [46.23427, -111.77734], [46.98024, -113.18923], [48.7259, -113.36019], [48.62806, -114.70049], [45.62631, -114.34303]]
res_3 = airportsInPolygon(airports_3, polygon_3)
expected_3 = [True, False, True, False, False, False, True, True, True]
print("Result:", res_3)
print("Expected:", expected_3)
print("Passed:", res_3 == expected_3, "\n")

# Michigan/Indiana (email)
print("Michigan/Indiana")
airports_4 = ['I58', 'ANQ', 'OEB']
polygon_4 = [[41.75307, -85.130366], [41.75307, -84.901802], [41.628527, -85.130366], [41.628527, -84.901802]]
res_4 = airportsInPolygon(airports_4, polygon_4, False)
expected_4 = [True, True, False]
print("Result:", res_4)
print("Expected:", expected_4)
print("Passed:", res_4 == expected_4, "\n")

# Error Handling; invalid polygon
print("Error handling: invalid polygon")
airports_5 = ['I58', 'ANQ', 'OEB']
polygon_5 = [[41.75307, -85.130366], [41.75307, -84.901802]]
res_5 = airportsInPolygon(airports_5, polygon_5)
expected_5 = [False, False, False]
print("Result:", res_5)
print("Expected:", expected_5)
print("Passed:", res_5 == expected_5, "\n")

# Error Handling; invalid FAA id
print("Error handling: invalid FAA id")
airports_6 = ['I58', 'ANQ', 'OEB', 'ZZZ']
polygon_6 = [[41.75307, -85.130366], [41.75307, -84.901802], [41.628527, -85.130366], [41.628527, -84.901802]]
res_6 = airportsInPolygon(airports_6, polygon_6, False)
expected_6 = [True, True, False, False]
print("Result:", res_6)
print("Expected:", expected_6)
print("Passed:", res_6 == expected_6, "\n")