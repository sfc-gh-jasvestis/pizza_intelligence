"""
Shared routing utilities for Pizza Demo
Ensures all apps show consistent route data using OSRM
"""

import requests
from typing import List, Tuple, Optional
import time

# Cache for route data (keyed by start/end coords)
_route_cache = {}
_cache_ttl = 300  # 5 minutes

def get_route_from_osrm(start_lon: float, start_lat: float, 
                        end_lon: float, end_lat: float,
                        use_cache: bool = True) -> Tuple[List[List[float]], int, int]:
    """
    Get actual road route from OSRM routing service.
    
    Returns:
        Tuple of (route_coords, duration_seconds, distance_meters)
        route_coords is list of [lon, lat] pairs
    """
    cache_key = f"{start_lon:.6f},{start_lat:.6f}_{end_lon:.6f},{end_lat:.6f}"
    
    # Check cache
    if use_cache and cache_key in _route_cache:
        cached = _route_cache[cache_key]
        if time.time() - cached["time"] < _cache_ttl:
            return cached["coords"], cached["duration"], cached["distance"]
    
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("routes") and len(data["routes"]) > 0:
                route = data["routes"][0]
                coords = route["geometry"]["coordinates"]
                duration = int(route.get("duration", 0))
                distance = int(route.get("distance", 0))
                
                # Cache the result
                _route_cache[cache_key] = {
                    "coords": coords,
                    "duration": duration,
                    "distance": distance,
                    "time": time.time()
                }
                
                return coords, duration, distance
    except Exception as e:
        print(f"OSRM route fetch error: {e}")
    
    # Fallback: straight line
    return [[start_lon, start_lat], [end_lon, end_lat]], 0, 0


def get_driver_position_on_route(route_coords: List[List[float]], 
                                  progress: float) -> Tuple[float, float]:
    """
    Calculate driver position along route based on progress (0.0 to 1.0).
    
    Returns:
        Tuple of (lat, lon)
    """
    if not route_coords or len(route_coords) < 2:
        return None, None
    
    # Clamp progress to valid range
    progress = max(0.0, min(1.0, progress))
    
    # Calculate total route length
    total_distance = 0
    segments = []
    for i in range(len(route_coords) - 1):
        dx = route_coords[i+1][0] - route_coords[i][0]
        dy = route_coords[i+1][1] - route_coords[i][1]
        dist = (dx**2 + dy**2) ** 0.5
        segments.append({
            "start": route_coords[i], 
            "end": route_coords[i+1], 
            "dist": dist
        })
        total_distance += dist
    
    if total_distance == 0:
        return route_coords[0][1], route_coords[0][0]
    
    # Find position at given progress
    target_distance = progress * total_distance
    traveled = 0
    
    for seg in segments:
        if traveled + seg["dist"] >= target_distance:
            # Position is within this segment
            seg_progress = (target_distance - traveled) / seg["dist"] if seg["dist"] > 0 else 0
            lon = seg["start"][0] + seg_progress * (seg["end"][0] - seg["start"][0])
            lat = seg["start"][1] + seg_progress * (seg["end"][1] - seg["start"][1])
            return lat, lon
        traveled += seg["dist"]
    
    # At end of route
    return route_coords[-1][1], route_coords[-1][0]


def interpolate_simple_position(store_lat: float, store_lon: float,
                                 customer_lat: float, customer_lon: float,
                                 progress: float) -> Tuple[float, float]:
    """
    Simple linear interpolation fallback when route is not available.
    
    Returns:
        Tuple of (lat, lon)
    """
    progress = max(0.0, min(1.0, progress))
    lat = store_lat + (customer_lat - store_lat) * progress
    lon = store_lon + (customer_lon - store_lon) * progress
    return lat, lon
