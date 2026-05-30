import httpx
import os
import json

IAM_URL = "https://iam.cloud.ibm.com/identity/token"


async def _get_iam_token(api_key: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            IAM_URL,
            data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": api_key},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        return r.json()["access_token"]


async def call_supervisor(message: str) -> dict:
    api_key = os.getenv("WATSONX_APIKEY")
    base_url = os.getenv("ORCHESTRATE_URL", "https://us-south.watson-orchestrate.cloud.ibm.com")
    agent_id = os.getenv("ORCHESTRATE_AGENT_ID", "")

    if not api_key:
        return {"error": "WATSONX_APIKEY not set", "response": None}

    try:
        token = await _get_iam_token(api_key)
    except Exception as e:
        return {"error": f"IAM token fetch failed: {e}", "response": None}

    candidate_endpoints = [
        f"{base_url}/api/v1/orchestrate/runs/stream",
        f"{base_url}/v1/orchestrate/runs/stream",
        f"https://api.us-south.watson-orchestrate.cloud.ibm.com/api/v1/orchestrate/runs/stream",
    ]

    base_payload = {"message": {"role": "user", "content": message}}
    payloads = []
    if agent_id:
        payloads.append({**base_payload, "agent_id": agent_id})
    payloads.append(base_payload)

    full_text = ""
    last_error = None

    for endpoint in candidate_endpoints:
        for payload in payloads:
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    async with client.stream(
                        "POST",
                        endpoint,
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                        },
                    ) as resp:
                        if resp.status_code >= 400:
                            body = await resp.aread()
                            last_error = f"HTTP {resp.status_code} at {endpoint}: {body.decode()[:300]}"
                            continue
                        async for line in resp.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data = line[6:].strip()
                            if data == "[DONE]":
                                break
                            try:
                                event = json.loads(data)
                                if event.get("event") == "message.delta":
                                    full_text += event.get("data", {}).get("content", "")
                            except json.JSONDecodeError:
                                continue
                if full_text:
                    return {"response": full_text, "agent": "frazilwatch_supervisor", "error": None}
            except Exception as e:
                last_error = str(e)
                continue

    return {"error": last_error, "response": None}
