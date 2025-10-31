"""
Geocoding utility to convert addresses to latitude/longitude coordinates.
Uses Nominatim (OpenStreetMap) for free geocoding without API keys.
"""

import requests
import time
from typing import Optional, Tuple

def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Convert an address string to latitude/longitude coordinates.

    Args:
        address: Full address string (e.g., "123 Main St, New York, NY 10001")

    Returns:
        Tuple of (latitude, longitude) if successful, None if failed
    """
    if not address or not address.strip():
        return None

    try:
        # Use Nominatim (OpenStreetMap) geocoding service
        # Free and doesn't require API key
        url = "https://nominatim.openstreetmap.org/search"

        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }

        headers = {
            'User-Agent': 'RouteOptimizationPlatform/1.0'  # Required by Nominatim
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            results = response.json()

            if results and len(results) > 0:
                lat = float(results[0]['lat'])
                lon = float(results[0]['lon'])
                return (lat, lon)

        return None

    except Exception as e:
        print(f"Geocoding error for address '{address}': {str(e)}")
        return None


def batch_geocode_addresses(addresses: list) -> dict:
    """
    Geocode multiple addresses with rate limiting.

    Args:
        addresses: List of address strings

    Returns:
        Dictionary mapping addresses to (lat, lon) tuples
    """
    results = {}

    for address in addresses:
        coords = geocode_address(address)
        results[address] = coords

        # Rate limiting: Nominatim allows 1 request per second
        time.sleep(1.1)

    return results


def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validate that latitude and longitude are within valid ranges.

    Args:
        lat: Latitude value
        lon: Longitude value

    Returns:
        True if valid, False otherwise
    """
    if lat is None or lon is None:
        return False

    # Valid ranges: lat [-90, 90], lon [-180, 180]
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return True

    return False


def format_coordinates(lat: float, lon: float, precision: int = 6) -> str:
    """
    Format coordinates as a string.

    Args:
        lat: Latitude
        lon: Longitude
        precision: Number of decimal places

    Returns:
        Formatted string like "40.758896, -73.985130"
    """
    if lat is None or lon is None:
        return "Unknown"

    return f"{lat:.{precision}f}, {lon:.{precision}f}"
