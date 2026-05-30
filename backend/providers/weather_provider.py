import httpx
from datetime import datetime
from typing import Optional

BASE_URL = "https://api.weather.gc.ca"
HEADERS = {"User-Agent": "FrazilWatch/1.0 (MUN IBM Hackathon; promitd@mun.ca)"}

CANDIDATE_STATIONS = [
    {"id": "8400413", "field": "STATION_ID", "name": "Bay d'Espoir area"},
    {"id": "8402427", "field": "STATION_ID", "name": "St. Alban's, NL"},
    {"id": "8400500", "field": "STATION_ID", "name": "Gaultois, NL"},
]


async def _fetch_station(station_id: str, field: str) -> Optional[dict]:
    url = f"{BASE_URL}/collections/climate-hourly/items"
    params = {field: station_id, "limit": 1, "sortby": "-LOCAL_DATE", "f": "json"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, params=params, headers=HEADERS)
        r.raise_for_status()
        features = r.json().get("features", [])
        return features[0]["properties"] if features else None


async def get_weather(lat: float, lon: float) -> dict:
    for station in CANDIDATE_STATIONS:
        try:
            obs = await _fetch_station(station["id"], station["field"])
            if obs and obs.get("TEMP") is not None:
                temp = float(obs["TEMP"])
                wind = float(obs.get("WIND_SPD") or 0)
                return {
                    "location": station["name"],
                    "coordinates": {"lat": lat, "lon": lon},
                    "timestamp": obs.get("LOCAL_DATE", datetime.utcnow().isoformat()),
                    "air_temp_c": temp,
                    "wind_speed_kmh": wind,
                    "wind_direction": str(obs.get("WIND_DIR", "N/A")),
                    "forecast_summary": _summary(temp, wind),
                    "data_quality": "real",
                    "source": "Environment Canada MSC GeoMet",
                    "station_id": station["id"],
                }
        except Exception:
            continue

    return {
        "location": f"Bay d'Espoir area ({lat:.2f}N {abs(lon):.2f}W)",
        "coordinates": {"lat": lat, "lon": lon},
        "timestamp": datetime.utcnow().isoformat(),
        "air_temp_c": -5.0,
        "wind_speed_kmh": 15.0,
        "wind_direction": "NW",
        "forecast_summary": "Estimated values — Environment Canada API unavailable",
        "data_quality": "fallback",
        "source": "FrazilWatch fallback estimator",
        "note": "Live API unreachable; using conservative estimates",
    }


def _summary(temp: float, wind: float) -> str:
    t = "Extremely cold" if temp <= -15 else "Cold" if temp <= -8 else "Near freezing" if temp <= 0 else "Above freezing"
    w = "very strong winds" if wind >= 40 else "strong winds" if wind >= 20 else "moderate winds" if wind >= 10 else "light winds"
    return f"{t}, {w}"
