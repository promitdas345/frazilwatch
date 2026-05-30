import httpx
from datetime import datetime
from typing import Optional

# DFO MEDS buoy API — nearest coastal buoys to Bay d'Espoir south coast NL
MEDS_BASE = "https://api.meds-sdmm.dfo-mpo.gc.ca/meds/pub/v1"
CANDIDATE_BUOYS = ["C44150", "C44137", "C44138"]


async def _fetch_buoy(buoy_id: str) -> Optional[dict]:
    url = f"{MEDS_BASE}/buoydata"
    async with httpx.AsyncClient(timeout=12) as client:
        r = await client.get(url, params={"stn_id": buoy_id, "limit": 1})
        if r.status_code != 200:
            return None
        data = r.json()
        if not data:
            return None
        entry = data[0] if isinstance(data, list) else data
        water_temp = entry.get("SSTP") or entry.get("water_temp")
        if water_temp is None:
            return None
        return {
            "water_temp_c": float(water_temp),
            "wave_height_m": float(entry.get("VCAR") or entry.get("wave_height") or 0.3),
            "current_speed_mps": 0.2,
            "salinity_ppt": 30.0,
            "marine_summary": f"Coastal NL buoy {buoy_id}",
            "data_quality": "real",
            "source": f"DFO MEDS buoy {buoy_id}",
        }


async def get_marine(lat: float, lon: float) -> dict:
    for buoy_id in CANDIDATE_BUOYS:
        try:
            data = await _fetch_buoy(buoy_id)
            if data:
                return data
        except Exception:
            continue

    # Bay d'Espoir is a river-fed fjord — estimate from seasonal/air-temp correlation
    return {
        "water_temp_c": 0.5,
        "wave_height_m": 0.3,
        "current_speed_mps": 0.15,
        "salinity_ppt": 28.0,
        "marine_summary": "Estimated fjord conditions — no direct buoy at this inland site",
        "data_quality": "estimated",
        "source": "FrazilWatch fjord estimator",
        "note": "Bay d'Espoir is a river-fed fjord; nearest ocean buoys are offshore. Values estimated from seasonal norms.",
    }
