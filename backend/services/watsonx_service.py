import os
import httpx
from typing import Optional

WATSONX_API_KEY = os.getenv("WATSONX_API_KEY") or os.getenv("WATSONX_APIKEY")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_MODEL_ID = os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-8b-instruct")
IAM_URL = "https://iam.cloud.ibm.com/identity/token"


async def _iam_token() -> Optional[str]:
    if not WATSONX_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                IAM_URL,
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": WATSONX_API_KEY,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            return r.json().get("access_token") if r.status_code == 200 else None
    except Exception:
        return None


async def enhance_with_watsonx(report: dict, risk: dict) -> dict:
    if not WATSONX_API_KEY or not WATSONX_PROJECT_ID:
        report["ai_enhanced"] = False
        report["narrative"] = _fallback(report, risk)
        report["ai_source"] = "local_template (no credentials)"
        return report

    token = await _iam_token()
    if not token:
        report["ai_enhanced"] = False
        report["narrative"] = _fallback(report, risk)
        report["ai_source"] = "local_template (IAM token failed)"
        return report

    prompt = _prompt(report, risk)
    url = f"{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29"
    payload = {
        "model_id": WATSONX_MODEL_ID,
        "project_id": WATSONX_PROJECT_ID,
        "input": prompt,
        "parameters": {
            "max_new_tokens": 250,
            "temperature": 0.3,
            "stop_sequences": ["---", "\n\n\n"],
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
        if r.status_code == 200:
            text = r.json().get("results", [{}])[0].get("generated_text", "").strip()
            report["ai_enhanced"] = True
            report["narrative"] = text or _fallback(report, risk)
            report["ai_source"] = f"watsonx.ai {WATSONX_MODEL_ID}"
            return report
    except Exception:
        pass

    report["ai_enhanced"] = False
    report["narrative"] = _fallback(report, risk)
    report["ai_source"] = "local_template (watsonx call failed)"
    return report


def _prompt(report: dict, risk: dict) -> str:
    level = risk.get("risk_level", "UNKNOWN")
    score = risk.get("risk_score", 0)
    factors = [f["factor"] for f in risk.get("contributing_factors", []) if f.get("triggered")]
    grid = report.get("grid_summary", "")
    protocol = report.get("protocol", "MONITOR")

    return f"""You are an AI advisor for NL Hydro's grid operations center. Write a concise situation report for a human operator.

Frazil Ice Risk — Bay d'Espoir Hydroelectric Station
Risk Level: {level} (score {score}/100)
Active risk factors: {', '.join(factors) if factors else 'none'}
Grid state: {grid}
Protocol activated: {protocol}

Write 2-3 sentences: what the risk means, why the grid state matters, what action is being requested. Plain English. No jargon. Readable in 30 seconds.

Situation report:"""


def _fallback(report: dict, risk: dict) -> str:
    level = risk.get("risk_level", "LOW")
    score = risk.get("risk_score", 0)
    grid = risk.get("grid_state", {})
    lil = grid.get("lil_load_mw", 781)
    ceil = grid.get("lil_ceiling_mw", 785)
    protocol = report.get("protocol", "MONITOR")

    if level == "HIGH":
        return (
            f"Frazil ice formation is predicted at Bay d'Espoir intakes within approximately 6 hours "
            f"(risk score {score}/100). "
            f"The Labrador-Island Link is at {lil}/{ceil} MW — effectively at its ceiling — "
            f"so increasing LIL transfer to cover a Bay d'Espoir loss is physically blocked. "
            f"The {protocol} protocol is activated; human operator approval is required before any action is taken."
        )
    if level == "ELEVATED":
        return (
            f"Conditions at Bay d'Espoir are approaching frazil formation thresholds (risk score {score}/100). "
            f"No immediate grid action required, but monitoring should be increased "
            f"and response equipment made ready."
        )
    return (
        f"Current conditions at Bay d'Espoir present low frazil ice risk (score {score}/100). "
        f"Standard monitoring protocol is in effect. No grid action required."
    )
