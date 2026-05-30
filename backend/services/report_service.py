from datetime import datetime


def compile_report(weather: dict, marine: dict, risk: dict, recommendations: dict) -> dict:
    grid = risk.get("grid_state", {})
    lil = grid.get("lil_load_mw", 0)
    ceil = grid.get("lil_ceiling_mw", 785)
    demand = grid.get("island_demand_mw", 0)
    bde = grid.get("bde_capacity_mw", 604)

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "report_type": "FRAZIL_ICE_RISK_ASSESSMENT",
        "location": "Bay d'Espoir Hydroelectric Station, Newfoundland",
        "risk_level": risk.get("risk_level", "UNKNOWN"),
        "risk_score": risk.get("risk_score", 0),
        "weather_summary": weather.get("forecast_summary", ""),
        "marine_summary": marine.get("marine_summary", ""),
        "grid_summary": (
            f"LIL: {lil}/{ceil} MW ({ceil - lil} MW headroom). "
            f"Island demand: {demand} MW. BdE at risk: {bde} MW."
        ),
        "protocol": recommendations.get("protocol", "MONITOR"),
        "action_count": len(recommendations.get("actions", [])),
        "human_approval_required": recommendations.get("human_approval_required", False),
        "ai_enhanced": False,
        "narrative": None,
        "ai_source": None,
    }
