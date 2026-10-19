"""
Geospatial Logistics & Transit Optimization Engine for AnnRakshak AI.
Computes great-circle Haversine distances between food donors and NGO distribution hubs in Prayagraj.
Calculates realistic urban transit times assuming standard 20 km/h city traffic speed
to prevent cold-chain and food safety window violations during surplus food recovery.
"""

import math
from typing import Dict, Any, List, Optional, Tuple

# Earth radius in kilometers
EARTH_RADIUS_KM = 6371.0

# Standard urban recovery vehicle transit speed (km/h) for Prayagraj city traffic
DEFAULT_CITY_SPEED_KMH = 20.0

# Known geographical hubs in Prayagraj for localization fallback
PRAYAGRAJ_HUBS = {
    "civil_lines": {"name": "Civil Lines", "lat": 25.4520, "lng": 81.8340},
    "tagore_town": {"name": "Tagore Town", "lat": 25.4480, "lng": 81.8560},
    "katra": {"name": "Katra / University", "lat": 25.4630, "lng": 81.8460},
    "chowk": {"name": "Chowk / MG Marg", "lat": 25.4358, "lng": 81.8463},
    "naini": {"name": "Naini Shelter Hub", "lat": 25.4080, "lng": 81.8680},
    "daraganj": {"name": "Daraganj Depot", "lat": 25.4320, "lng": 81.8750}
}

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two GPS coordinates using the Haversine formula.
    Returns distance in kilometers.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = EARTH_RADIUS_KM * c
    return round(distance, 2)

# Convenient aliases
calculate_haversine_distance = haversine_distance_km

def estimate_transit_time_minutes(distance_km: float, speed_kmh: float = DEFAULT_CITY_SPEED_KMH) -> int:
    """
    Estimates vehicle transit time in minutes given distance and average city speed (default 20 km/h).
    Minimum 2 minutes if distance > 0.
    """
    if distance_km <= 0:
        return 0
    effective_speed = max(5.0, min(60.0, float(speed_kmh)))
    minutes = (distance_km / effective_speed) * 60.0
    return max(2, int(math.ceil(minutes)))

estimate_transit_minutes = estimate_transit_time_minutes

def sort_listings_by_distance(
    listings: List[Dict[str, Any]],
    viewer_lat: float = 25.4358,
    viewer_lng: float = 81.8463,
    speed_kmh: float = DEFAULT_CITY_SPEED_KMH
) -> List[Dict[str, Any]]:
    """
    Annotates donation listings with distance (km) and estimated transit time (mins)
    relative to the viewing NGO's base coordinates, then sorts them nearest-first.
    """
    annotated = []
    for item in listings:
        listing = dict(item)
        d_lat = float(listing.get("lat") or 25.4520)
        d_lng = float(listing.get("lng") or 81.8340)

        dist = haversine_distance_km(viewer_lat, viewer_lng, d_lat, d_lng)
        transit_mins = estimate_transit_time_minutes(dist, speed_kmh)

        listing["distance_km"] = dist
        listing["transit_time_mins"] = transit_mins
        listing["routing_summary"] = f"{dist:.1f} km away (~{transit_mins} mins via 20 km/h city route)"
        annotated.append(listing)

    # Sort ascending by distance
    annotated.sort(key=lambda x: x["distance_km"])
    return annotated
