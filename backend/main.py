from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from providers.weather_provider import get_weather
from providers.marine_provider import get_marine
from services.risk_engine import (
    calculate_risk,
    LIL_CEILING_MW,
    LIL_LOAD_MW,
    ISLAND_DEMAND_MW,
    BDE_CAPACITY_MW,
    MARITIME_HEADROOM_MW,
)
from services.recommendation_engine import get_recommendations
from services.report_service import compile_report
from services.watsonx_service import enhance_with_watsonx
from services.orchestrate_service import call_supervisor

_public_url = os.getenv("PUBLIC_URL", "http://localhost:8000")

app = FastAPI(
    title="FrazilWatch API",
    version="1.0.0",
    servers=[{"url": _public_url, "description": "FrazilWatch backend"}],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo scenario: January 2026 reference conditions (the real event)
DEMO_WEATHER = {
    "location": "Bay d'Espoir, NL",
    "coordinates": {"lat": 47.93, "lon": -55.75},
    "timestamp": "2026-01-15T18:00:00Z",
    "air_temp_c": -12.0,
    "wind_speed_kmh": 28.0,
    "wind_direction": "NW",
    "forecast_summary": "Extremely cold, strong northwest winds",
    "data_quality": "demo",
    "source": "FrazilWatch Demo (Jan 2026 reference conditions)",
}
DEMO_MARINE = {
    "water_temp_c": 0.3,
    "wave_height_m": 0.8,
    "current_speed_mps": 0.22,
    "salinity_ppt": 28.0,
    "marine_summary": "Near-freezing water with active turbulence — high frazil nucleation potential",
    "data_quality": "demo",
    "source": "FrazilWatch Demo (Jan 2026 reference conditions)",
}


class LocationInput(BaseModel):
    lat: float = 47.93
    lon: float = -55.75
    location_name: str = "Bay d'Espoir, NL"
    demo_mode: bool = False


class WeatherInput(BaseModel):
    lat: float = 47.93
    lon: float = -55.75
    demo_mode: bool = False


class MarineInput(BaseModel):
    lat: float = 47.93
    lon: float = -55.75
    demo_mode: bool = False


class RiskInput(BaseModel):
    weather: dict
    marine: dict


class RecommendationInput(BaseModel):
    risk: dict
    weather: dict
    marine: dict


class ReportInput(BaseModel):
    weather: dict
    marine: dict
    risk: dict
    recommendations: dict


class FrazilRiskInput(BaseModel):
    location: str = "Bay d'Espoir"
    demo_mode: bool = False


@app.get("/health")
def health():
    return {"status": "ok", "service": "FrazilWatch API", "version": "1.0.0"}


@app.post("/tools/weather")
async def tool_weather(input: WeatherInput):
    """IBM Orchestrate Weather Agent calls this endpoint."""
    if input.demo_mode:
        return DEMO_WEATHER
    return await get_weather(input.lat, input.lon)


@app.post("/tools/marine")
async def tool_marine(input: MarineInput):
    """IBM Orchestrate Marine Agent calls this endpoint."""
    if input.demo_mode:
        return DEMO_MARINE
    return await get_marine(input.lat, input.lon)


@app.post("/tools/risk")
async def tool_risk(input: RiskInput):
    """IBM Orchestrate Frazil Risk Agent calls this endpoint."""
    return calculate_risk(input.weather, input.marine)


@app.post("/tools/recommendations")
async def tool_recommendations(input: RecommendationInput):
    """IBM Orchestrate Operations Advisor Agent calls this endpoint."""
    return get_recommendations(input.risk, input.weather, input.marine)


@app.post("/tools/report")
async def tool_report(input: ReportInput):
    """IBM Orchestrate Report Agent calls this endpoint."""
    report = compile_report(input.weather, input.marine, input.risk, input.recommendations)
    return await enhance_with_watsonx(report, input.risk)


@app.post("/tools/get_frazil_risk")
async def tool_get_frazil_risk(input: FrazilRiskInput):
    """IBM Orchestrate Climatology Agent calls this endpoint."""
    if input.demo_mode:
        weather, marine = DEMO_WEATHER, DEMO_MARINE
    else:
        weather, marine = await asyncio.gather(
            get_weather(47.93, -55.75),
            get_marine(47.93, -55.75),
        )
    risk = calculate_risk(weather, marine)
    level = risk["risk_level"]
    temp = weather.get("air_temp_c", 0)
    wind = weather.get("wind_speed_kmh", 0)

    if level == "HIGH":
        window_hours = 6
        explanation = (
            f"Air temperature {temp}°C and wind {wind} km/h exceed both frazil "
            f"thresholds. Frazil ice formation predicted at Bay d'Espoir intakes "
            f"within approximately {window_hours} hours."
        )
    elif level == "ELEVATED":
        window_hours = 12
        explanation = (
            f"Conditions approaching frazil threshold (air {temp}°C, wind {wind} km/h). "
            f"Risk is elevated — continued monitoring required."
        )
    else:
        window_hours = None
        explanation = (
            f"Current conditions (air {temp}°C, wind {wind} km/h) are below frazil "
            f"thresholds. No immediate risk detected."
        )

    return {
        "risk_level": level,
        "risk_score": risk["risk_score"],
        "temperature_c": temp,
        "wind_speed_kmh": wind,
        "water_temp_c": marine.get("water_temp_c"),
        "window_hours": window_hours,
        "explanation": explanation,
        "data_quality": weather.get("data_quality", "real"),
        "source": weather.get("source"),
    }


@app.post("/tools/get_lil_load")
def tool_get_lil_load():
    """IBM Orchestrate Dispatch Agent calls this endpoint."""
    headroom = LIL_CEILING_MW - LIL_LOAD_MW
    within_35 = headroom <= 35
    status = (
        f"MAXED — only {headroom} MW headroom. LIL cannot absorb additional load without trip risk."
        if within_35
        else f"LIL has {headroom} MW headroom. Additional transfer is feasible."
    )
    return {
        "lil_load_mw": LIL_LOAD_MW,
        "lil_ceiling_mw": LIL_CEILING_MW,
        "lil_headroom_mw": headroom,
        "within_35mw_ceiling": within_35,
        "status": status,
        "data_quality": "simulated",
        "note": "NL Hydro SCADA telemetry is proprietary — these values are simulated for the demo.",
    }


@app.post("/tools/get_maritime_headroom")
def tool_get_maritime_headroom():
    """IBM Orchestrate Dispatch Agent calls this endpoint."""
    return {
        "available_import_mw": MARITIME_HEADROOM_MW,
        "contract_rate_available": True,
        "status": (
            f"Maritime Link has {MARITIME_HEADROOM_MW} MW import headroom available. "
            f"Contract rate can be secured before spot-market pricing activates."
        ),
        "data_quality": "simulated",
        "note": "NL Hydro SCADA telemetry is proprietary — these values are simulated for the demo.",
    }


@app.post("/tools/get_bde_unit_status")
def tool_get_bde_unit_status():
    """IBM Orchestrate Dispatch Agent calls this endpoint."""
    current_gen = round(BDE_CAPACITY_MW * 0.99)  # near-capacity in demo state
    return {
        "bay_despoir_capacity_mw": BDE_CAPACITY_MW,
        "current_generation_mw": current_gen,
        "unit_status": "ONLINE — all units generating at near-capacity",
        "island_demand_mw": ISLAND_DEMAND_MW,
        "lil_ceiling_mw": LIL_CEILING_MW,
        "summary": (
            f"Bay d'Espoir generating {current_gen}/{BDE_CAPACITY_MW} MW. "
            f"Island demand is {ISLAND_DEMAND_MW} MW. "
            f"Loss of BdE would require {BDE_CAPACITY_MW} MW to be sourced elsewhere immediately."
        ),
        "data_quality": "simulated",
        "note": "NL Hydro SCADA telemetry is proprietary — these values are simulated for the demo.",
    }


@app.post("/analyze-risk")
async def analyze_risk(input: LocationInput):
    """
    Full pipeline endpoint. The frontend calls this; in production IBM Orchestrate
    chains the individual /tools/* endpoints instead.
    """
    if input.demo_mode:
        weather, marine = DEMO_WEATHER, DEMO_MARINE
    else:
        weather, marine = await asyncio.gather(
            get_weather(input.lat, input.lon),
            get_marine(input.lat, input.lon),
        )

    risk = calculate_risk(weather, marine)
    recommendations = get_recommendations(risk, weather, marine)
    report_data = compile_report(weather, marine, risk, recommendations)
    final_report = await enhance_with_watsonx(report_data, risk)

    return {
        "location": input.location_name,
        "coordinates": {"lat": input.lat, "lon": input.lon},
        "demo_mode": input.demo_mode,
        "weather": weather,
        "marine": marine,
        "risk": risk,
        "recommendations": recommendations,
        "report": final_report,
        "agent_workflow": [
            {
                "agent": "Weather Agent",
                "status": "complete",
                "tool_endpoint": "POST /tools/weather",
                "description": "Fetched live Environment Canada weather data",
            },
            {
                "agent": "Marine Agent",
                "status": "complete",
                "tool_endpoint": "POST /tools/marine",
                "description": "Retrieved marine and water temperature conditions",
            },
            {
                "agent": "Frazil Risk Agent",
                "status": "complete",
                "tool_endpoint": "POST /tools/risk",
                "description": "Computed deterministic frazil ice risk score",
            },
            {
                "agent": "Operations Advisor Agent",
                "status": "complete",
                "tool_endpoint": "POST /tools/recommendations",
                "description": "Applied grid constraint rules, issued action protocol",
            },
            {
                "agent": "Report Agent",
                "status": "complete",
                "tool_endpoint": "POST /tools/report",
                "description": "Generated situation report via watsonx.ai Llama 3",
            },
        ],
        "orchestrated_by": "IBM watsonx Orchestrate",
    }


class OrchestrateInput(BaseModel):
    message: str
    demo_mode: bool = False


@app.post("/orchestrate-chat")
async def orchestrate_chat(input: OrchestrateInput):
    """Call the frazilwatch_supervisor agent in IBM watsonx Orchestrate."""
    if input.demo_mode:
        message = (
            "Check the current frazil ice risk at Bay d'Espoir and recommend grid action. "
            "Use these conditions: air temperature -12°C, wind 28 km/h, water temperature 0.3°C. "
            "The Labrador-Island Link is at 781 MW against a 785 MW ceiling and island demand is 1450 MW. "
            "Execute the full response protocol."
        )
    else:
        message = input.message or "Check the current frazil ice risk at Bay d'Espoir and recommend grid action."

    return await call_supervisor(message)
