import random

FRAZIL_TEMP_C = -8.0
FRAZIL_WIND_KMH = 20.0
LIL_CEILING_MW = 785
LIL_LOAD_MW = 781       # demo state — near ceiling
ISLAND_DEMAND_MW = 1450
BDE_CAPACITY_MW = 604
MARITIME_HEADROOM_MW = 380


def calculate_risk(weather: dict, marine: dict) -> dict:
    temp = float(weather.get("air_temp_c", 0))
    wind = float(weather.get("wind_speed_kmh", 0))
    water_temp = float(marine.get("water_temp_c", 5))
    wave_height = float(marine.get("wave_height_m", 0))

    temp_score = min(40, max(0, abs(min(temp, 0)) * 2))
    wind_score = min(30, wind * 0.75)
    water_score = min(20, max(0, (4 - water_temp) * 5)) if water_temp < 4 else 0
    turbulence_score = min(10, wave_height * 5 + wind * 0.2)
    total = min(100, temp_score + wind_score + water_score + turbulence_score)

    cold = temp <= FRAZIL_TEMP_C
    windy = wind >= FRAZIL_WIND_KMH
    near_freeze = water_temp <= 2.0

    if cold and windy:
        level = "HIGH"
    elif cold or windy or near_freeze:
        level = "ELEVATED"
    else:
        level = "LOW"

    factors = [
        {
            "factor": "Air temperature",
            "value": f"{temp}°C",
            "threshold": f"≤ {FRAZIL_TEMP_C}°C",
            "triggered": cold,
        },
        {
            "factor": "Wind speed",
            "value": f"{wind} km/h",
            "threshold": f"≥ {FRAZIL_WIND_KMH} km/h",
            "triggered": windy,
        },
        {
            "factor": "Water temperature",
            "value": f"{water_temp}°C",
            "threshold": "≤ 2°C",
            "triggered": near_freeze,
        },
    ]

    return {
        "risk_score": round(total, 1),
        "risk_level": level,
        "contributing_factors": factors,
        "grid_cells": _grid_cells(total),
        "grid_state": {
            "lil_load_mw": LIL_LOAD_MW,
            "lil_ceiling_mw": LIL_CEILING_MW,
            "lil_headroom_mw": LIL_CEILING_MW - LIL_LOAD_MW,
            "lil_is_maxed": (LIL_CEILING_MW - LIL_LOAD_MW) <= 35,
            "island_demand_mw": ISLAND_DEMAND_MW,
            "bde_capacity_mw": BDE_CAPACITY_MW,
            "maritime_headroom_mw": MARITIME_HEADROOM_MW,
        },
        "thresholds": {
            "air_temp_c": FRAZIL_TEMP_C,
            "wind_kmh": FRAZIL_WIND_KMH,
        },
        "scoring_breakdown": {
            "temperature": round(temp_score, 1),
            "wind": round(wind_score, 1),
            "water_temperature": round(water_score, 1),
            "turbulence": round(turbulence_score, 1),
        },
    }


_CELL_LABELS = [
    ["Reservoir NW", "Reservoir NE", "Upper Intake", "Ridge"],
    ["Open Water W", "Main Channel", "Primary Intake", "Cliff Face"],
    ["Lower Channel", "Intake Bay", "BdE Intake", "Eastern Arm"],
    ["Outflow S", "Tailrace", "Downstream", "South Channel"],
]
_INTAKE_CELLS = {(1, 2), (2, 2)}


def _grid_cells(base_score: float) -> list:
    rng = random.Random(42)
    cells = []
    for row in range(4):
        for col in range(4):
            is_intake = (row, col) in _INTAKE_CELLS
            score = max(0, min(100, base_score + rng.uniform(-10, 12) + (20 if is_intake else 0)))
            cells.append({
                "row": row,
                "col": col,
                "label": _CELL_LABELS[row][col],
                "risk_score": round(score, 1),
                "risk_level": "HIGH" if score >= 60 else "ELEVATED" if score >= 30 else "LOW",
                "is_intake": is_intake,
            })
    return cells
