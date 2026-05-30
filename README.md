# FrazilWatch

Predictive multi-agent system for frazil ice risk at Bay d'Espoir, NL.
Built on IBM watsonx Orchestrate + llama-3-3-70b-instruct. IBM × MUN Hackathon 2026 — Team Namles.

---

## Architecture

```
React Frontend
    └─► POST /analyze-risk  (FastAPI)
            ├─► POST /tools/weather       ◄── IBM Orchestrate Weather Agent
            ├─► POST /tools/marine        ◄── IBM Orchestrate Marine Agent
            ├─► POST /tools/risk          ◄── IBM Orchestrate Frazil Risk Agent
            ├─► POST /tools/recommendations ◄── IBM Orchestrate Operations Advisor Agent
            └─► POST /tools/report        ◄── IBM Orchestrate Report Agent → watsonx.ai Llama 3
```

IBM Orchestrate contains the real agents. The backend exposes tool endpoints that Orchestrate agents call. The frontend calls `/analyze-risk` which chains all tools in sequence.

---

## Backend Setup

**Windows PowerShell (run each line separately):**
```powershell
cd "c:\Users\Promit\Desktop\IBM Watson hackathon\backend"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --port 8000
```

**Mac/Linux:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

API available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### Environment Variables (backend/.env)

| Variable | Source |
|---|---|
| `WATSONX_API_KEY` | IBM Cloud → Manage → API keys |
| `WATSONX_PROJECT_ID` | watsonx.ai → project → Manage tab |
| `WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` (default) |
| `WATSONX_MODEL_ID` | `meta-llama/llama-3-3-70b-instruct` (default) |

Without credentials the backend still works — it uses a local template for the report narrative.

---

## Frontend Setup

**Windows PowerShell (open a second terminal, run each line separately):**
```powershell
cd "c:\Users\Promit\Desktop\IBM Watson hackathon\frontend"
npm install
npm run dev
```

**Mac/Linux:**
```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:5173`.

---

## IBM Orchestrate Tool Endpoints

### Agent-facing tools (register these in Orchestrate)

These are the tools the YAML agents call directly. Each maps to one tool name in the agent definition.

| Tool name (in YAML) | Endpoint | Agent | What it does |
|---|---|---|---|
| `get_frazil_risk` | `POST /tools/get_frazil_risk` | climatology_agent | Fetches live EC weather, calculates frazil risk (LOW/ELEVATED/HIGH) |
| `get_lil_load` | `POST /tools/get_lil_load` | dispatch_agent | Returns Labrador-Island Link load vs 785 MW ceiling |
| `get_maritime_headroom` | `POST /tools/get_maritime_headroom` | dispatch_agent | Returns Maritime Link available import headroom |
| `get_bde_unit_status` | `POST /tools/get_bde_unit_status` | dispatch_agent | Returns Bay d'Espoir unit status and island demand |

#### `POST /tools/get_frazil_risk`
```json
{ "location": "Bay d'Espoir", "demo_mode": false }
```
Response:
```json
{
  "risk_level": "LOW | ELEVATED | HIGH",
  "risk_score": 85.2,
  "temperature_c": -12.0,
  "wind_speed_kmh": 28.0,
  "water_temp_c": 0.3,
  "window_hours": 6,
  "explanation": "Air temperature -12°C and wind 28 km/h exceed both frazil thresholds...",
  "data_quality": "real"
}
```

#### `POST /tools/get_lil_load`
No input required.
```json
{
  "lil_load_mw": 781,
  "lil_ceiling_mw": 785,
  "lil_headroom_mw": 4,
  "within_35mw_ceiling": true,
  "status": "MAXED — only 4 MW headroom. LIL cannot absorb additional load without trip risk.",
  "data_quality": "simulated"
}
```

#### `POST /tools/get_maritime_headroom`
No input required.
```json
{
  "available_import_mw": 380,
  "contract_rate_available": true,
  "status": "Maritime Link has 380 MW import headroom available at contract rate.",
  "data_quality": "simulated"
}
```

#### `POST /tools/get_bde_unit_status`
No input required.
```json
{
  "bay_despoir_capacity_mw": 604,
  "current_generation_mw": 598,
  "unit_status": "ONLINE — all units generating at near-capacity",
  "island_demand_mw": 1450,
  "data_quality": "simulated"
}
```

### Pipeline tools (internal / frontend use)

| Endpoint | What it does |
|---|---|
| `POST /tools/weather` | Fetches live EC MSC GeoMet weather data |
| `POST /tools/marine` | Gets marine/water temp (DFO buoy or estimated) |
| `POST /tools/risk` | Deterministic frazil score from weather + marine |
| `POST /tools/recommendations` | Applies grid constraint rules, issues action protocol |
| `POST /tools/report` | Compiles report, calls watsonx.ai for narrative |

### Request shapes (pipeline tools)

**`/tools/weather`** and **`/tools/marine`**
```json
{ "lat": 47.93, "lon": -55.75, "demo_mode": false }
```

**`/tools/risk`**
```json
{ "weather": { ...weather response... }, "marine": { ...marine response... } }
```

**`/tools/recommendations`**
```json
{ "risk": { ... }, "weather": { ... }, "marine": { ... } }
```

**`/tools/report`**
```json
{ "weather": { ... }, "marine": { ... }, "risk": { ... }, "recommendations": { ... } }
```

---

## Demo Mode

Pass `"demo_mode": true` to `/analyze-risk` (or the individual tool endpoints) to use the January 2026 reference conditions: air -12°C, wind 28 km/h NW, water 0.3°C. This triggers HIGH risk and the ALTERNATIVE_RESPONSE protocol (LIL maxed at 781/785 MW, obvious fix blocked).

Real weather data in May will return LOW risk — use Demo Mode for the judging video.

---

## Data Sources

| Data | Source | Type |
|---|---|---|
| Weather | Environment Canada MSC GeoMet OGC API | Real (no key needed) |
| Marine | DFO MEDS buoy network | Real when available |
| Marine fallback | FrazilWatch fjord estimator | Estimated |
| Grid telemetry | Built-in constants (NL Hydro SCADA is proprietary) | Simulated |
| Risk reasoning | watsonx.ai llama-3-3-70b-instruct | AI-enhanced |

Every field in the API response includes a `data_quality` label: `real`, `estimated`, `fallback`, or `demo`.
