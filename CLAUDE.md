# CLAUDE.md — FrazilWatch (read this first, every session)

You are helping build **FrazilWatch**, a proof-of-concept multi-agent AI system
for the IBM x MUN watsonx Hackathon (Team Namles). Read this whole file before
acting. Re-read it at the start of each session.

---

## What we are building (in one paragraph)

A predictive multi-agent system on **IBM watsonx Orchestrate** that detects
frazil-ice formation at the Bay d'Espoir hydroelectric plant in Newfoundland
using **real live Environment Canada weather data**, then resolves a conflict
between frazil risk and grid-capacity limits to recommend a pre-emptive grid
response. Three specialist agents (Climatology, Dispatch) plus a Supervisor
that makes the final decision. Reasoning model is `llama-3-1-70b-instruct`.
The internal grid telemetry is **simulated** via a Python MCP server (NL Hydro's
real SCADA is proprietary — simulation is the honest, intended approach).

The "wow" moment: the Supervisor REJECTS the obvious fix ("send more power down
the Labrador-Island Link") because that link is maxed at its 785 MW ceiling, and
instead issues an alternative protocol — pre-emptive offload + Maritime Link
import + industrial load-shed + public conservation alert.

---

## CRITICAL operating rules for you (Claude Code)

1. **The IBM watsonx Orchestrate ADK changes frequently. Do NOT trust your
   training data for ADK commands or YAML schema.** Before running ANY
   `orchestrate` CLI command or finalizing any agent YAML, check the current
   syntax with `orchestrate --help`, `orchestrate <subcommand> --help`, and the
   live docs at https://developer.watson-orchestrate.ibm.com/. If a command or
   field is rejected, the fix is almost always a renamed field/flag — look it up,
   don't guess repeatedly.

2. **Never invent or hardcode secrets.** API keys, project IDs, and instance URLs
   live in `.env` (see SETUP.md) and are filled by a human. If a value is missing,
   STOP and tell the user which `.env` variable to set. Do not fabricate keys.

3. **Real vs simulated data is a hard line.**
   - Weather data is REAL: `weather_tool.py` hits the live Environment Canada API.
   - Grid telemetry is SIMULATED: `grid_mcp_server.py` returns mock JSON.
   - Never blur these. Never fake the weather data to make a demo work — if the
     live API fails, fix the API call or the station ID, don't stub it out.

4. **Verify the data source before building on it.** If `verify_station.py` has
   not been confirmed to return recent data for the chosen station, run it (or
   ask the user to run it on a machine with internet — the station ID may need
   to change). All downstream work assumes real data flows.

5. **No personal data, no client data, no scraped social media.** Hackathon rule.
   Only public Environment Canada data + our own simulated grid data.

6. **Scope discipline.** The minimum winning product is: the three agents running
   end-to-end IN the Orchestrate chat UI, triggered by real weather data,
   producing the Supervisor's JSON action manifest + plain-English justification.
   The React dashboard is a BONUS. Do not spend time on the frontend until the
   agent chain works in the Orchestrate chat. Do not over-engineer the frazil
   model — a clean threshold that fires on real data beats a complex one.

7. **When unsure, ask.** This is a supervised pair-programming session, not an
   autonomous run. Surface decisions (especially anything touching the IBM
   environment) to Promit or Hassan rather than guessing.

---

## Build order (do these in sequence)

1. **Confirm environment** — Python 3.11–3.13, Docker running, `.env` filled.
   See SETUP.md. Do not proceed until `orchestrate` CLI responds.
2. **Verify data** — `python verify_station.py` returns recent temp/wind. If the
   candidate station fails, pick a working one from its output and update
   `STATION_ID` / `STATION_FIELD` in `weather_tool.py`.
3. **Tools** — get `weather_tool.py` (real) and `grid_mcp_server.py` (simulated)
   working standalone. Test each returns sensible output.
4. **Register tools with the ADK** — import the weather tool as a Python tool and
   the grid server as an MCP toolkit. Verify with `orchestrate --help` for exact
   commands; see SETUP.md for the intended sequence.
5. **Agents** — import `climatology_agent.yaml`, `dispatch_agent.yaml`, then
   `supervisor_agent.yaml` (supervisor last, since it references the others as
   collaborators). Deploy.
6. **Test the chain** — in the Orchestrate chat, trigger the Supervisor and
   confirm it calls Climatology → (if HIGH) Dispatch → applies the deterministic
   rule → outputs the JSON manifest. THIS IS THE MVP.
7. **Tune the Supervisor prompt** — make the JSON output and justification clean
   and judge-readable. See `supervisor_prompt.md` if present.
8. **(Bonus, only if MVP works) Frontend** — FastAPI wrapper + React dashboard.

---

## The locked demo scenario (build toward exactly this)

- Climatology: live data shows air ≤ -8°C, wind ≥ 20 km/h, open water →
  risk_level HIGH → "frazil predicted within ~6 hours."
- Dispatch: LIL at 781 MW (ceiling 785) → maxed; island demand ~1450 MW →
  "cannot absorb Bay d'Espoir loss by increasing LIL transfer."
- Supervisor: deterministic rule fires → rejects LIL increase → issues
  alternative protocol → outputs `action_manifest.json` + justification.

Numbers that matter: **785 MW** (LIL ceiling), **6 hours** (lead time),
**604 MW** (Bay d'Espoir at risk), **1967** (last full BdE shutdown before 2026).

To force the demo conflict, the simulated state in `grid_mcp_server.py` is
already set to LIL=781, demand=1450. Leave it there for the demo.

---

## Key facts (verified, safe to rely on)

- Reasoning model string: `watsonx/meta-llama/llama-3-1-70b-instruct`
- Llama 3 emits a `<|tool_call|>` token before its JSON tool-call payload; if
  serving via vLLM, the parser flags are `--enable-auto-tool-choice` and
  `--tool-call-parser llama3_json`. (Inside Orchestrate this is handled for you.)
- Environment Canada OGC API base: `https://api.weather.gc.ca/` — no key needed,
  supports CQL2 filtering and `f=csv`. Collections: `climate-hourly`,
  `climate-stations`, `hydrometric-stations`.
- ADK install: `pip install --upgrade ibm-watsonx-orchestrate`, Developer
  Edition runs on `http://localhost:4321`, needs Docker + ~16GB RAM.

---

## File map

```
/                       repo root
  CLAUDE.md             this file
  SETUP.md              exact setup commands + .env template
  requirements.txt      Python deps
  .env                  secrets (human-filled, gitignored, NEVER commit)
  tools/
    weather_tool.py     REAL Environment Canada frazil-risk tool
    grid_mcp_server.py  SIMULATED grid telemetry MCP server
  agents/
    climatology_agent.yaml
    dispatch_agent.yaml
    supervisor_agent.yaml
  scripts/
    verify_station.py   run FIRST — confirms the data source
  prompts/
    supervisor_prompt.md  (reference for the Supervisor's logic)
  frontend/             (bonus, only if MVP works)
```

Adjust paths if the repo differs, but keep tools / agents / scripts separated.

---

## Definition of done (MVP)

Running the Supervisor in the Orchestrate chat, with real weather flowing in,
produces: a frazil-risk read → a grid-capacity read → the deterministic
decision → a JSON action manifest with a clear justification. If that works,
you have a demonstrable, judge-ready system. Everything else is polish.
