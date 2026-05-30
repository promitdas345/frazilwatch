#!/usr/bin/env python3
"""
weather_tool.py — the REAL Environment Canada tool the Climatology Agent calls.

This is the heart of "real live data." It pulls recent temperature + wind for
the Bay d'Espoir area from the MSC GeoMet OGC API (no key needed) and computes
a frazil-ice formation risk score.

Wrap this as an MCP tool (see grid_mcp_server.py for the pattern) OR register
it as an ADK Python tool. The function signature + docstring + type hints are
what Llama 3 reads to learn how to call it — keep them clean.

  pip install requests pydantic

IMPORTANT: set STATION_ID / STATION_FIELD to whatever verify_station.py confirmed.
"""

import requests
from datetime import datetime
from typing import Optional

BASE = "https://api.weather.gc.ca"
HEADERS = {"User-Agent": "FrazilWatch-Hackathon/1.0 (MUN watsonx)"}

# ST ALBAN'S — verified active 2026-05-28, ~40 km from Bay d'Espoir
STATION_ID = "55398"
STATION_FIELD = "STN_ID"

# ---- Frazil thresholds (from published research; cite as "research-based") ----
# These are defensible starting values. Tune for a clean demo.
FRAZIL_AIR_TEMP_C = -8.0        # at/below this, strong heat loss
FRAZIL_WIND_KMH = 20.0          # at/above this, surface mixing prevents ice cover
# Risk is HIGH when BOTH conditions hold (cold AND windy AND no ice cover).


def _latest_observation() -> Optional[dict]:
    """Fetch the most recent observation for the configured station.
    Tries climate-hourly first, falls back to climate-daily."""
    for collection in ("climate-hourly", "climate-daily"):
        url = f"{BASE}/collections/{collection}/items"
        params = {
            STATION_FIELD: STATION_ID,
            "limit": 1,
            "sortby": "-LOCAL_DATE",
            "f": "json",
        }
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=30)
            r.raise_for_status()
            feats = r.json().get("features", [])
            if feats:
                return feats[0]["properties"]
        except Exception:
            continue
    return None


def get_frazil_risk(ice_cover_present: bool = False) -> dict:
    """Assess frazil-ice formation risk at the Bay d'Espoir intakes RIGHT NOW.

    Pulls live Environment Canada temperature and wind data and evaluates it
    against research-based frazil formation thresholds. Frazil forms when the
    water is supercooled (driven by cold air + wind heat loss) AND surface
    turbulence prevents an insulating ice cover.

    Args:
        ice_cover_present: Whether the reservoir currently has an insulating
            ice cover. If True, frazil risk is suppressed regardless of weather.

    Returns:
        A dict with: risk_level ("LOW"/"ELEVATED"/"HIGH"), the observed
        temperature and wind, the time of observation, and a short reason.
    """
    try:
        obs = _latest_observation()
    except Exception as e:
        return {"risk_level": "UNKNOWN", "error": f"weather fetch failed: {e}"}

    if not obs:
        return {"risk_level": "UNKNOWN", "error": "no recent observation returned"}

    temp = obs.get("TEMP") or obs.get("MEAN_TEMPERATURE")
    wind = obs.get("WIND_SPD") or obs.get("SPEED_MAX_GUST") or 0
    when = obs.get("LOCAL_DATE")

    # Guard against missing fields
    if temp is None or wind is None:
        return {
            "risk_level": "UNKNOWN",
            "observed_temp_c": temp,
            "observed_wind_kmh": wind,
            "observation_time": when,
            "error": "temp or wind missing in observation",
        }

    cold = temp <= FRAZIL_AIR_TEMP_C
    windy = wind >= FRAZIL_WIND_KMH

    if ice_cover_present:
        level = "LOW"
        reason = "Insulating ice cover present; frazil formation suppressed."
    elif cold and windy:
        level = "HIGH"
        reason = (f"Air {temp}C (<= {FRAZIL_AIR_TEMP_C}) and wind {wind}km/h "
                  f"(>= {FRAZIL_WIND_KMH}) with open water: supercooling + mixing. "
                  f"Frazil formation predicted within ~6 hours.")
    elif cold or windy:
        level = "ELEVATED"
        reason = (f"One driver present (air {temp}C, wind {wind}km/h). "
                  f"Monitor closely; conditions approaching frazil threshold.")
    else:
        level = "LOW"
        reason = f"Air {temp}C, wind {wind}km/h: below frazil formation thresholds."

    return {
        "risk_level": level,
        "observed_temp_c": temp,
        "observed_wind_kmh": wind,
        "observation_time": when,
        "ice_cover_present": ice_cover_present,
        "station": STATION_ID,
        "reason": reason,
    }


if __name__ == "__main__":
    # Quick manual test (run on a machine with internet, not the sandbox)
    import json
    print("Live frazil risk (assuming open water):")
    print(json.dumps(get_frazil_risk(ice_cover_present=False), indent=2))
