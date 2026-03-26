"""
Geographic and geometric utility functions
"""
from typing import List, Tuple, Optional
import logging
from config.settings import PRECISION_RADIUS_MAP


def calculate_precision_radius(precision_bits: Optional[int]) -> Optional[float]:
    """
    Calculate radius in meters based on precision_bits
    Lower precision_bits means less precision (larger radius)
    """
    if precision_bits is None:
        return None
    
    # Return the radius from our mapping, defaulting to 0 for unknown values
    return PRECISION_RADIUS_MAP.get(precision_bits, 0)


def convex_hull(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Calculate the convex hull of a set of 2D points using Graham scan algorithm
    
    Args:
        points: List of (x, y) coordinate tuples
        
    Returns:
        List of points forming the convex hull
    """
    def cross_product(o: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    
    points = sorted(set(tuple(p) for p in points))
    if len(points) <= 1:
        return points
    
    # Build lower hull
    lower = []
    for p in points:
        while len(lower) >= 2 and cross_product(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    
    # Build upper hull
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross_product(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    
    return lower[:-1] + upper[:-1]


def create_polygon_from_nodes(node_positions: List[Tuple[float, float]]) -> Optional[List[List[float]]]:
    """
    Create a polygon from a list of node positions using convex hull
    
    Args:
        node_positions: List of (lat, lon) tuples
        
    Returns:
        List of [lat, lon] pairs forming the polygon, or None if insufficient points
    """
    if len(node_positions) < 3:
        return None
    
    try:
        hull_points = convex_hull(node_positions)
        # Convert back to list of [lat, lon] pairs
        polygon_coords = [[float(p[0]), float(p[1])] for p in hull_points]
        return polygon_coords
    except Exception as e:
        logging.warning(f"Could not create polygon from nodes: {e}")
        return None
