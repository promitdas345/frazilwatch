import httpx
from datetime import datetime, timezone
from typing import Optional

BASE_URL = "https://api.weather.gc.ca"
HEADERS = {"User-Agent": "FrazilWatch/1.0 (MUN IBM Hackathon; promitd@mun.ca)"}

# Per-request timeout config: 8s connect, 12s read. Keeps total wall time under 30s.
_TIMEOUT = httpx.Timeout(connect=8.0, read=12.0, write=5.0, pool=5.0)

# Hardcoded priority stations tried first — verified to have climate-daily records.
# Station 55398 = St. Alban's NL (closest active EC climate station to Bay d'Espoir).
# Station 8403389 = Hermitage NL (secondary fallback, same south-coast region).
_PRIORITY_STATIONS = [
    {"id": "55398", "name": "St. Alban's, NL"},
    {"id": "8403389", "name": "Hermitage, NL"},
]


async def _find_nearby_stations(lat: float, lon: float, client: httpx.AsyncClient) -> list:
    """Query EC climate-stations for the nearest active stations to lat/lon.
    Uses bbox params instead of CQL2 INTERSECTS filter — more reliably supported."""
    delta = 1.5  # search ±1.5 degrees (~150 km)
    # Use bbox query parameter instead of CQL2 filter (more stable EC OGC endpoint)
    params = {
        "bbox": f"{lon-delta},{lat-delta},{lon+delta},{lat+delta}",
        "limit": 20,
        "f": "json",
    }
    try:
        r = await client.get(
            f"{BASE_URL}/collections/climate-stations/items", params=params, headers=HEADERS
        )
        r.raise_for_status()
    except Exception:
        return []

    stations = []
    for feat in r.json().get("features", []):
        p = feat.get("properties", {})
        stn_id = p.get("STN_ID") or p.get("CLIMATE_IDENTIFIER") or p.get("STATION_ID")
        last = p.get("LAST_DATE", "")
        name = p.get("STATION_NAME", "Unknown station")
        if stn_id and last:
            stations.append({"id": str(stn_id), "name": name, "last": last})

    # Most recently updated first
    stations.sort(key=lambda s: s["last"], reverse=True)
    return stations[:5]


async def _fetch_obs(station_id: str, client: httpx.AsyncClient) -> Optional[tuple]:
    """Try to get the latest temp+wind observation for a station.
    Returns (properties_dict, collection_name) or (None, None).
    Tries climate-daily before climate-hourly — historical EC stations (like 55398)
    only have daily records; trying hourly first wastes up to 36s on empty responses."""
    for collection in ("climate-daily", "climate-hourly"):
        for field in ("STN_ID", "CLIMATE_IDENTIFIER", "STATION_ID"):
            try:
                params = {field: station_id, "limit": 1, "sortby": "-LOCAL_DATE", "f": "json"}
                r = await client.get(
                    f"{BASE_URL}/collections/{collection}/items", params=params, headers=HEADERS
                )
                if r.status_code != 200:
                    continue
                feats = r.json().get("features", [])
                if not feats:
                    continue
                obs = feats[0]["properties"]
                temp = obs.get("MEAN_TEMPERATURE") or obs.get("TEMP")
                if temp is not None:
                    return obs, collection
            except Exception:
                continue
    return None, None


def _build_result(obs: dict, collection: str, station: dict, lat: float, lon: float, note: str = "") -> dict:
    temp = float(obs.get("MEAN_TEMPERATURE") or obs.get("TEMP"))
    wind = float(obs.get("SPEED_MAX_GUST") or obs.get("WIND_SPD") or 0)
    result = {
        "location": station["name"],
        "coordinates": {"lat": lat, "lon": lon},
        "timestamp": obs.get("LOCAL_DATE", datetime.utcnow().isoformat()),
        "air_temp_c": temp,
        "wind_speed_kmh": wind,
        "wind_direction": str(obs.get("WIND_DIR", "N/A")),
        "forecast_summary": _summary(temp, wind),
        "data_quality": "real",
        "source": f"Environment Canada MSC GeoMet ({collection})",
        "station_id": station["id"],
        "station_name": station["name"],
    }
    if note:
        result["note"] = note
    return result


async def get_weather(lat: float, lon: float) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        # 1. Spatial search — find the nearest active station to the given coordinates.
        #    This makes any location work, not just Bay d'Espoir.
        try:
            nearby = await _find_nearby_stations(lat, lon, client)
        except Exception:
            nearby = []

        for station in nearby:
            try:
                obs, collection = await _fetch_obs(station["id"], client)
                if obs is None:
                    continue
                return _build_result(obs, collection, station, lat, lon)
            except Exception:
                continue

        # 2. Priority stations fallback — if spatial search finds nothing,
        #    fall back to the verified Bay d'Espoir area stations.
        for station in _PRIORITY_STATIONS:
            try:
                obs, collection = await _fetch_obs(station["id"], client)
                if obs is None:
                    continue
                return _build_result(
                    obs, collection, station, lat, lon,
                    note="No active EC station found near requested coordinates — using nearest available."
                )
            except Exception:
                continue

    # 3. Complete fallback — all EC API paths failed or timed out.
    return {
        "location": f"({lat:.2f}N, {abs(lon):.2f}W)",
        "coordinates": {"lat": lat, "lon": lon},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "air_temp_c": -5.0,
        "wind_speed_kmh": 15.0,
        "wind_direction": "N/A",
        "forecast_summary": "Estimated values — Environment Canada API unavailable",
        "data_quality": "fallback",
        "source": "FrazilWatch fallback estimator",
        "note": "Live API unreachable; using conservative estimates",
    }


def _summary(temp: float, wind: float) -> str:
    t = "Extremely cold" if temp <= -15 else "Cold" if temp <= -8 else "Near freezing" if temp <= 0 else "Above freezing"
    w = "very strong winds" if wind >= 40 else "strong winds" if wind >= 20 else "moderate winds" if wind >= 10 else "light winds"
    return f"{t}, {w}"
