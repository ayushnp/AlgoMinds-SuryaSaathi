import numpy as np
import math
from typing import Tuple, List

# --- Constants ---
# Conversions
SQFT_TO_M2 = 0.092903  # 1 sq. ft = 0.092903 sq. meters
# Earth's radius (mean) for accurate distance calculations
EARTH_RADIUS_M = 6371000


def get_meters_to_degrees(lat: float) -> Tuple[float, float]:
    """Calculates degrees per meter for both latitude and longitude at a given latitude."""
    # Latitude (approximate 1 degree in meters is constant)
    m_per_deg_lat = 111111.0  # 111.111 km

    # Longitude (1 degree in meters varies by latitude)
    m_per_deg_lon = (math.cos(math.radians(lat)) * 2 * math.pi * EARTH_RADIUS_M) / 360

    degrees_per_meter_lat = 1 / m_per_deg_lat
    degrees_per_meter_lon = 1 / m_per_deg_lon

    return degrees_per_meter_lat, degrees_per_meter_lon


def calculate_buffer_polygon(lat: float, lon: float, radius_m: float) -> np.ndarray:
    """
    Calculates a simple bounding box polygon (4 corners) representing the search area.

    Returns a 4x2 numpy array representing the bounding box polygon
    [[lat1, lon1], [lat2, lon2], ...].
    """
    deg_per_m_lat, deg_per_m_lon = get_meters_to_degrees(lat)

    # Calculate half-side length in degrees
    delta_lat = radius_m * deg_per_m_lat
    delta_lon = radius_m * deg_per_m_lon

    # Define the 4 corners (a square approximation of the buffer area)
    polygon = np.array([
        [lat - delta_lat, lon - delta_lon],  # Bottom-Left
        [lat - delta_lat, lon + delta_lon],  # Bottom-Right
        [lat + delta_lat, lon + delta_lon],  # Top-Right
        [lat + delta_lat, lon - delta_lon]  # Top-Left
    ])

    return polygon


def polygon_to_bbox_string(polygon: np.ndarray) -> str:
    """Encodes the polygon coordinates as a simple string for the JSON output."""
    # For robust production use, consider Well-Known Text (WKT) format,
    # but a simple list of coordinates is used here.
    return str(polygon.tolist())