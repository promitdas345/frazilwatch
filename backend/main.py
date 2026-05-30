from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from dotenv import load_dotenv

load_dotenv()

from providers.weather_provider import get_weather
from providers.marine_provider import get_marine
from services.risk_engine import calculate_risk
from services.recommendation_engine import get_recommendations
from services.report_service import compile_report
from services.watsonx_service import enhance_with_watsonx

app = FastAPI(title="FrazilWatch API", version="1.0.0")

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
                "description": "Generated situation report via watsonx.ai Granite",
            },
        ],
        "orchestrated_by": "IBM watsonx Orchestrate",
    }
