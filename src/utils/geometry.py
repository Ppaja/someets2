# src/utils/geometry.py

def is_point_in_polygon(point, polygon):
    """
    Prüft, ob ein Punkt innerhalb eines Polygons liegt, mittels Ray-Casting-Algorithmus.
    
    :param point: Ein Tupel (x, z) für den zu prüfenden Punkt.
    :param polygon: Eine Liste von Tupeln [(x1, z1), (x2, z2), ...], die die Ecken des Polygons definieren.
    :return: True, wenn der Punkt im Polygon ist, sonst False.
    """
    x, z = point
    n = len(polygon)
    inside = False

    p1x, p1z = polygon[0]
    for i in range(n + 1):
        p2x, p2z = polygon[i % n]
        if z > min(p1z, p2z):
            if z <= max(p1z, p2z):
                if x <= max(p1x, p2x):
                    if p1z != p2z:
                        xinters = (z - p1z) * (p2x - p1x) / (p2z - p1z) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1z = p2x, p2z

    return inside