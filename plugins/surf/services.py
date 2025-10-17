"""
Surf Plugin Services - Wave data fetching from Open-Meteo Marine API
"""
import logging
import sqlite3
import requests
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Open-Meteo Marine API (free, no API key required)
MARINE_API = "https://marine-api.open-meteo.com/v1/marine"


def fetch_surf(lat: float, lon: float) -> Optional[Tuple[float, float, float]]:
    """
    Fetch wave data from Open-Meteo Marine API
    
    Args:
        lat: Latitude of surf spot
        lon: Longitude of surf spot
        
    Returns:
        Tuple of (wave_height_m, wave_period_s, wave_direction_deg) or None if failed
    """
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "wave_height,wave_period,wave_direction"
        }
        
        response = requests.get(MARINE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current", {})
        wave_height = current.get("wave_height")
        wave_period = current.get("wave_period")
        wave_direction = current.get("wave_direction")
        
        if wave_height is not None and wave_period is not None and wave_direction is not None:
            logger.info(f"🌊 Fetched surf data for ({lat}, {lon}): {wave_height}m @ {wave_period}s from {wave_direction}°")
            return (float(wave_height), float(wave_period), float(wave_direction))
        else:
            logger.warning(f"Incomplete wave data from API for ({lat}, {lon})")
            return None
            
    except Exception as e:
        logger.error(f"Failed to fetch surf data for ({lat}, {lon}): {e}")
        return None


def update_surf_cache(spot_id: int, lat: float, lon: float) -> bool:
    """
    Fetch wave data and update cache for a specific spot
    
    Args:
        spot_id: ID of surf spot
        lat: Latitude
        lon: Longitude
        
    Returns:
        True if successful, False otherwise
    """
    surf_data = fetch_surf(lat, lon)
    if not surf_data:
        return False
    
    height, period, direction = surf_data
    
    try:
        with sqlite3.connect("data/cameronpad_dev.db") as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO surf_cache(spot_id, height_m, period_s, direction_deg, ts)
                VALUES(?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (spot_id, height, period, direction))
            conn.commit()
            logger.info(f"💾 Updated surf cache for spot ID {spot_id}")
            return True
    except Exception as e:
        logger.error(f"Failed to update surf cache: {e}")
        return False


def update_all_spots():
    """
    Fetch and update wave data for all surf spots
    This should be called periodically by a background task
    """
    try:
        with sqlite3.connect("data/cameronpad_dev.db") as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT id, name, lat, lon FROM surf_spots")
            spots = cur.fetchall()
        
        if not spots:
            logger.debug("No surf spots to update")
            return
        
        logger.info(f"🔄 Updating surf data for {len(spots)} spots...")
        success_count = 0
        
        for spot in spots:
            if update_surf_cache(spot["id"], spot["lat"], spot["lon"]):
                success_count += 1
        
        logger.info(f"✅ Updated {success_count}/{len(spots)} surf spots successfully")
        
    except Exception as e:
        logger.error(f"Failed to update all surf spots: {e}")
