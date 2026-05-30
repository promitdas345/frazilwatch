# FrazilWatch

Predictive multi-agent system for frazil ice risk at Bay d'Espoir, NL.
Built on IBM watsonx Orchestrate + Granite-3.0-8B-Instruct. IBM × MUN Hackathon 2026 — Team Namles.

---

## Architecture

```
React Frontend
    └─► POST /analyze-risk  (FastAPI)
            ├─► POST /tools/weather       ◄── IBM Orchestrate Weather Agent
            ├─► POST /tools/marine        ◄── IBM Orchestrate Marine Agent
            ├─► POST /tools/risk          ◄── IBM Orchestrate Frazil Risk Agent
            ├─► POST /tools/recommendations ◄── IBM Orchestrate Operations Advisor Agent
            └─► POST /tools/report        ◄── IBM Orchestrate Report Agent → watsonx.ai Granite
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
| `WATSONX_MODEL_ID` | `ibm/granite-3-8b-instruct` (default) |

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

Each endpoint is registered as a tool in IBM Orchestrate and called by the corresponding agent:

| Endpoint | Orchestrate Agent | What it does |
|---|---|---|
| `POST /tools/weather` | Weather Agent | Fetches live Environment Canada MSC GeoMet data for Bay d'Espoir area |
| `POST /tools/marine` | Marine Agent | Gets marine/water temp conditions (DFO buoy or estimated) |
| `POST /tools/risk` | Frazil Risk Agent | Deterministic frazil score from weather + marine data |
| `POST /tools/recommendations` | Operations Advisor Agent | Applies grid constraint rules, issues action protocol |
| `POST /tools/report` | Report Agent | Compiles report, calls watsonx.ai Granite for narrative |

### Request shapes

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
| Risk reasoning | watsonx.ai Granite-3.0-8B-Instruct | AI-enhanced |

Every field in the API response includes a `data_quality` label: `real`, `estimated`, `fallback`, or `demo`.
