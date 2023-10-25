import json
import math
import requests
from bs4 import BeautifulSoup


AIRPORTS_JSON_FILE = "airports.json"
PATHS_JSON_FILE = "paths.json"
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

# TODO
def main(src, dst, srcPolygon, dstPolygon):
    f = open(AIRPORTS_JSON_FILE)
    airports = json.load(f)
    f.close()

    srcPt = Point(src[0], src[1])
    dstPt = Point(dst[0], dst[1])

    srcXMin = min([x[0] for x in srcPolygon])
    srcXMax = max([x[0] for x in srcPolygon])
    srcYMin = min([x[1] for x in srcPolygon])
    srcYMax = max([x[1] for x in srcPolygon])

    dstXMin = min([x[0] for x in dstPolygon])
    dstXMax = max([x[0] for x in dstPolygon])
    dstYMin = min([x[1] for x in dstPolygon])
    dstYMax = max([x[1] for x in dstPolygon])
    
    srcAirportCandidates = []
    dstAirportCandidates = []

    for a in airports:
        if srcXMin <= a["LATITUDE"] <= srcXMax and srcYMin <= a["LONGITUDE"] <= srcYMax:
            srcAirportCandidates.append(a)
        if dstXMin <= a["LATITUDE"] <= dstXMax and dstYMin <= a["LONGITUDE"] <= dstYMax:
            dstAirportCandidates.append(a)

    inSrcPolygon = airportsInPolygon([x["IATA"] for x in srcAirportCandidates], srcPolygon)
    inDstPolygon = airportsInPolygon([x["IATA"] for x in dstAirportCandidates], dstPolygon)

    srcAirports = []
    for i, a in enumerate(inSrcPolygon):
        if a:
            srcAirports.append(srcAirportCandidates[i])

    dstAirports = []
    for i, a in enumerate(inDstPolygon):
        if a:
            dstAirports.append(dstAirportCandidates[i])


    minCost = 1000000 
    cheapestPath = None
    for a in srcAirports:
        cost = 0
        airportPt = Point(a["LATITUDE"], a["LONGITUDE"])
        distanceToSrcAirport = distance(srcPt, airportPt)
        cost += 100*distanceToSrcAirport

        for b in dstAirports:
            flightCost = getPathCost(a["IATA"], b["IATA"])
            cost += flightCost

            airportPt = Point(a["LATITUDE"], a["LONGITUDE"])
            distanceToDstAirport = distance(srcPt, airportPt)
            cost += 100*distanceToDstAirport

            if cost < minCost:
                minCost = cost
                cheapestPath = (a["IATA"], b["IATA"])

    carCost = 100*distance(srcPt, dstPt)

    if carCost < minCost:
        return "Car"
    print(cheapestPath)
    return cheapestPath


# Get distance between two points
def distance(pt1, pt2):
    return math.sqrt((pt1.x - pt2.x)**2 + (pt1.y - pt2.y)**2)


def getPathCost(src, dst):
    f = open(PATHS_JSON_FILE)
    paths = json.load(f)
    f.close()

    for p in paths:
        if p["Source"] == src and p["Dest"] == dst:
            return p["Fare"]
        
    return 100000000



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

    # print(airport_coords)

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

if __name__ == "__main__":
    start_coords = (38.8985429887236, -77.07207305396891)
    end_coords = (34.04863597668213, -118.26070003378426)
    start_polygon = [[39.32182563637547, -77.50982501611026], [39.61053089524596, -76.67408080949596], [39.00204638199489, -75.7835340135612], [38.15678657633557, -76.04287881965246], [38.08936304203749, -77.69027901242909], [38.82863488238268, -78.1964714444084], [39.32182563637547, -77.50982501611026]]
    dest_polygon =  [[34.13163757108633, -118.48221949026032], [34.230266472554284, -118.24737860668469], [34.14774079579688, -117.91125278895356], [33.75441790890569, -117.63077528348084], [33.37228445554111, -118.02817264622335], [33.69749764115173, -118.65066618058974], [34.13163757108633, -118.48221949026032]]
    main(start_coords, end_coords, start_polygon, dest_polygon)