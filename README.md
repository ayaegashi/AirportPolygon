# Airports in a Geographic Polygon

Author: Ayana Yaegashi

## How to use

### Input
- FAA Airport Identifiers (a list of strings, like ['I58', 'ANQ', 'OEB']).
- A geographic polygon (a list of lists of paired latitude/longitude points that define the outer bounds of the polygon).
- (Optional) a boolean indicating whether the polygon points are sorted or not. Note that concave polygons must be sorted. Default: True.

### Output
- A list of booleans where the i-th element in the return list indicates whether or not the i-th airport is in the polygon.


## Sources
https://stackoverflow.com/questions/217578/how-can-i-determine-whether-a-2d-point-is-within-a-polygon

https://www.geeksforgeeks.org/how-to-check-if-a-given-point-lies-inside-a-polygon/#

https://stackoverflow.com/questions/63926690/how-to-calculate-the-angle-between-two-points-in-python-3

