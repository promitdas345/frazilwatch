# SETUP.md — exact setup, in order

> Follow top to bottom. Steps marked **[HUMAN ONLY]** require IBM accounts/secrets
> and cannot be done by Claude Code. Do those first, then Claude Code can take over.

---

## Step 0 — [HUMAN ONLY] IBM Cloud + secrets

Done by Promit / Hassan (the two with environment seats):

1. Accept the IBM Cloud environment invite email (from the hackathon org).
2. Log into IBM Cloud with the SAME email used for the IBMid.
3. Open **watsonx.ai** → Developer Access panel. Copy:
   - the **project ID**
   - the **watsonx.ai endpoint URL** (ensure region = **Dallas / us-south**)
   - create and copy an **API key** (choose "Disable the leaked key")
4. Confirm **watsonx Orchestrate** launches from the Resource List.

Keep these values for the `.env` file in Step 3. Treat the API key like a password.

---

## Step 1 — Local prerequisites

- **Python 3.11–3.13** (NOT 3.14+, NOT 3.10 or lower). Check: `python --version`
- **Docker** installed and running, with `docker compose` available.
  (Rancher Desktop or Colima recommended on macOS/Linux.)
- ~16 GB RAM free for the Orchestrate Developer Edition (19 GB if using
  document processing — we are not, so 16 is fine).
- **Node.js 18+** (only needed for the bonus frontend).

---

## Step 2 — Python environment + ADK

```bash
# from repo root
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
pip install --upgrade ibm-watsonx-orchestrate    # the ADK + CLI

# confirm the CLI is alive (and learn the CURRENT command surface)
orchestrate --help
```

> If `orchestrate` is not found, re-check the venv is activated and the install
> succeeded. The CLI command surface is the source of truth for all later steps —
> READ ITS `--help` rather than assuming flags.

---

## Step 3 — [HUMAN ONLY] the `.env` file

Create `.env` at the repo root (it is gitignored — NEVER commit it). Fill the
placeholders with the values from Step 0:

```dotenv
# ---- watsonx.ai (for Llama 3 inference) ----
WATSONX_APIKEY=<your_ibm_cloud_api_key>
WATSONX_PROJECT_ID=<your_project_id>
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# ---- watsonx Orchestrate Developer Edition ----
# These come from the ADK docs / your Orchestrate instance.
WO_DEVELOPER_EDITION_SOURCE=orchestrate
WO_INSTANCE=<your_orchestrate_instance_url>
WO_API_KEY=<your_ibm_cloud_api_key>
```

> The exact WO_* variable names can shift between ADK versions. If the Developer
> Edition refuses to start, check the current required vars in the ADK docs
> (https://developer.watson-orchestrate.ibm.com/getting_started/installing) and
> update this file. Do not guess more than once — look it up.

---

## Step 4 — Verify the data source (run this BEFORE building)

```bash
python scripts/verify_station.py
```

- If it prints `✓ Station 8400413 works. LOCK IT.` → you're good.
- If it prints `✗ Candidate station unusable.` → pick a station from the listed
  fallbacks that shows `hourly=Y` and a RECENT `last` date, then edit
  `tools/weather_tool.py`: set `STATION_ID` and `STATION_FIELD` to match.
- Re-run until you get real recent temp/wind. **Do not proceed until this passes.**

```bash
# sanity-check the weather tool itself
python tools/weather_tool.py
```

---

## Step 5 — Start the Orchestrate Developer Edition

```bash
# starts the local Orchestrate (Docker). Exact command per `orchestrate --help`.
# Commonly:
orchestrate server start         # VERIFY the real subcommand via --help first
```

Wait until it reports ready (UI/API on http://localhost:4321).

---

## Step 6 — Register tools

> VERIFY exact commands with `orchestrate tools --help` and
> `orchestrate toolkits --help` — names below are the intended shape, not gospel.

```bash
# the simulated grid MCP server (run it, then import as an MCP toolkit)
# Option A: import as MCP toolkit (preferred)
orchestrate toolkits import --help     # READ THIS, then run the import it documents

# the real Environment Canada weather tool as a Python tool
orchestrate tools import --help        # READ THIS, then import tools/weather_tool.py
```

Confirm both tools appear:

```bash
orchestrate tools list
orchestrate toolkits list
```

---

## Step 7 — Register + deploy agents (supervisor LAST)

```bash
# import collaborators first, supervisor last (it references them)
orchestrate agents import -f agents/climatology_agent.yaml
orchestrate agents import -f agents/dispatch_agent.yaml
orchestrate agents import -f agents/supervisor_agent.yaml

orchestrate agents list
```

> If a YAML field is rejected (e.g. `collaborators`, `style`, `kind`), check the
> CURRENT agent schema in the ADK docs and adjust the YAML. This is the most
> likely place to hit version drift. One lookup, one fix.

Deploy / make available per the CLI's deploy command (check `--help`).

---

## Step 8 — Test the chain (this is the MVP gate)

In the Orchestrate chat UI (localhost:4321), talk to the **frazilwatch_supervisor**
agent. Prompt something like:

> "Check the current frazil ice risk at Bay d'Espoir and recommend grid action."

Expected flow:
1. Supervisor calls Climatology → gets HIGH risk (from real weather, or set the
   threshold/test conditions so it triggers).
2. Supervisor calls Dispatch → gets LIL maxed at 781/785, demand 1450.
3. Deterministic rule fires → Supervisor REJECTS "increase LIL" → issues the
   alternative protocol.
4. Output: a JSON action manifest + a plain-English justification.

If that happens, **the MVP is done.** Screenshot/record it — that's your demo.

---

## Step 9 — (BONUS, only if MVP works) Frontend

```bash
cd frontend
npm install
npm run dev          # FastAPI backend runs separately; see frontend/README
```

Do not start this until Step 8 passes.

---

## Troubleshooting quick hits

- **`orchestrate` command not found** → venv not activated / install failed.
- **Developer Edition won't start** → Docker not running, or wrong WO_* vars.
- **Agent import rejects a field** → ADK version drift; check docs, rename field.
- **Weather tool returns UNKNOWN/error** → wrong station ID/field; re-run
  `verify_station.py` and update `weather_tool.py`.
- **Llama 3 not tool-calling** → ensure the tool is actually attached to the
  agent and the agent `style: react`; check the tool description is clear.
- **403 from the weather API** → add/keep the User-Agent header (already in the
  code); confirm you're on a normal network, not a restricted one.
