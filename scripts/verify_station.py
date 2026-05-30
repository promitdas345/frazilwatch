#!/usr/bin/env python3
"""
verify_station.py  — RUN THIS FIRST (Hassan, hour 0)

Confirms that real, recent weather data comes back from Environment Canada
for the Bay d'Espoir area. This is the gate for the whole project.

If station 8400413 returns recent hourly temp/wind -> LOCKED, use it everywhere.
If not -> this script lists nearby stations so you can pick a live one in ~5 min.

No API key needed. Just: pip install requests
"""

import requests
import sys
from datetime import datetime, timedelta

BASE = "https://api.weather.gc.ca"

# Candidate station from the research. VERIFY don't trust.
CANDIDATE_STATION = "8400413"

# Bounding box around Bay d'Espoir / Meelpaeg Lake reservoir area.
# WKT requires longitude FIRST. (lon lat) pairs.
# Box roughly: lon -56.7..-55.6, lat 47.8..48.4
BDE_BBOX_WKT = "POLYGON((-56.7 47.8, -55.6 47.8, -55.6 48.4, -56.7 48.4, -56.7 47.8))"


# Some requests need a normal User-Agent or they get refused.
HEADERS = {"User-Agent": "FrazilWatch-Hackathon/1.0 (MUN watsonx)"}

# The station-ID field name on climate-hourly varies. Try each.
STATION_FIELDS = ["STATION_ID", "CLIMATE_IDENTIFIER", "STN_ID", "CLIMATE_ID"]


def check_candidate_station():
    """Try to pull recent hourly climate data for the candidate station.
    The API uses different field names for the station id depending on the
    collection version, so we try several."""
    print(f"\n[1] Checking candidate station {CANDIDATE_STATION} for recent hourly data...")
    url = f"{BASE}/collections/climate-hourly/items"
    for field in STATION_FIELDS:
        params = {
            field: CANDIDATE_STATION,
            "limit": 5,
            "sortby": "-LOCAL_DATE",
            "f": "json",
        }
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=30)
            if r.status_code != 200:
                continue
            feats = r.json().get("features", [])
            if not feats:
                continue
            print(f"    ✓ Field '{field}' worked. Got {len(feats)} records. Most recent:")
            for f in feats[:3]:
                p = f.get("properties", {})
                print(f"       {p.get('LOCAL_DATE')}  temp={p.get('TEMP')}C  "
                      f"wind={p.get('WIND_SPD')}km/h  dir={p.get('WIND_DIR')}")
            print(f"    -> Use query field '{field}={CANDIDATE_STATION}' in weather_tool.py")
            return True
        except Exception as e:
            print(f"    (field '{field}' errored: {e})")
            continue
    print(f"    ✗ No hourly records for {CANDIDATE_STATION} under any known field name.")
    print("      Likely a daily-only or inactive station — use a fallback from [2].")
    return False


def list_nearby_stations():
    """List climate stations in the Bay d'Espoir bounding box, so we can pick one."""
    print("\n[2] Listing climate stations near Bay d'Espoir (fallback options)...")
    url = f"{BASE}/collections/climate-stations/items"
    params = {
        "filter": f"INTERSECTS(geometry,{BDE_BBOX_WKT})",
        "limit": 50,
        "f": "json",
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        feats = data.get("features", [])
        if not feats:
            print("    ✗ No stations found in the box. Widen the bounding box.")
            return
        print(f"    Found {len(feats)} stations in the area:")
        for f in feats:
            p = f.get("properties", {})
            sid = p.get("STN_ID") or p.get("CLIMATE_IDENTIFIER") or p.get("STATION_ID")
            name = p.get("STATION_NAME", "?")
            first = p.get("FIRST_DATE", "?")
            last = p.get("LAST_DATE", "?")
            hourly = p.get("HAS_HOURLY_DATA", "?")
            print(f"       id={sid:<12} {name:<35} hourly={hourly}  last={last}")
        print("\n    -> Pick a station with hourly=Y and a RECENT last date.")
        print("       Use its ID in weather_tool.py and the agent config.")
    except Exception as e:
        print(f"    ✗ Request failed: {e}")


def check_hydrometric():
    """Confirm the hydrometric (water level/flow) API is reachable for the region."""
    print("\n[3] Checking hydrometric stations near Bay d'Espoir...")
    url = f"{BASE}/collections/hydrometric-stations/items"
    params = {
        "filter": f"INTERSECTS(geometry,{BDE_BBOX_WKT})",
        "limit": 20,
        "f": "json",
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        feats = r.json().get("features", [])
        if not feats:
            print("    ~ No hydrometric stations in the immediate box (OK — weather is the main trigger).")
            return
        print(f"    ✓ Found {len(feats)} hydrometric stations:")
        for f in feats[:10]:
            p = f.get("properties", {})
            print(f"       {p.get('STATION_NUMBER')}  {p.get('STATION_NAME')}")
    except Exception as e:
        print(f"    ~ Hydrometric check failed (non-blocking): {e}")


if __name__ == "__main__":
    print("=" * 64)
    print("  FrazilWatch — Environment Canada data source verification")
    print("=" * 64)

    ok = check_candidate_station()
    list_nearby_stations()
    check_hydrometric()

    print("\n" + "=" * 64)
    if ok:
        print(f"  RESULT: ✓ Station {CANDIDATE_STATION} works. LOCK IT. Tell the team.")
    else:
        print("  RESULT: ✗ Candidate station unusable.")
        print("  ACTION: Pick a station with hourly=Y + recent last date from the")
        print("          list above, and use that ID everywhere. ~5 minute fix.")
    print("=" * 64)
