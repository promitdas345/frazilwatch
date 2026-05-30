# FrazilWatch — Team Namles · 48-Hour Battle Plan
### IBM x MUN watsonx Hackathon · May 29–31, 2026

> **The one-liner:** A predictive multi-agent AI system that detects frazil-ice formation at Bay d'Espoir hours before it chokes the intakes, then autonomously coordinates the NL grid response — pre-emptive offload, Maritime Link imports, industrial load-shed, public conservation alert — before the lights go out. Built on watsonx Orchestrate + llama-3-3-70b-instruct, triggered by **real live Environment Canada data**.

---

## 0. The Non-Negotiable First Move (do this before anything else)

**Verify the data source.** Everything depends on whether real weather data comes back from Environment Canada for the Bay d'Espoir area. If it does, the whole project is grounded in real live data. If it doesn't, we fix it in 10 minutes by swapping the station — but only if we catch it now, not Sunday morning.

**Hassan runs `verify_station.py` (provided separately) in the first hour.** If station 8400413 returns recent hourly temp/wind data → locked. If not → he finds the nearest live hourly station near Meelpaeg Lake (48.24°N, 56.59°W) / Head of Bay d'Espoir (47.93°N, 55.75°W) and we use that ID everywhere.

---

## 1. What We're Building (the architecture in one picture)

```
   REAL LIVE DATA                    watsonx ORCHESTRATE                 OUTPUT
   ┌──────────────┐
   │ Env. Canada  │──temp/wind──▶ ┌─────────────────────┐
   │ MSC GeoMet   │               │ AGENT 1             │
   │ (real API)   │               │ Climatology         │──"frazil risk
   └──────────────┘               │ (frazil threshold)  │   in <6h"──┐
                                  └─────────────────────┘            │
   ┌──────────────┐                                                  ▼
   │ MCP SERVER   │──grid load──▶ ┌─────────────────────┐    ┌──────────────┐
   │ (simulated   │               │ AGENT 2             │    │ SUPERVISOR   │
   │  grid state) │               │ Dispatch            │───▶│ resolves the │
   └──────────────┘               │ (LIL vs 785MW)      │    │ conflict,    │
                                  └─────────────────────┘    │ acts via     │
                                                              │ Llama 3      │
                                                              └──────┬───────┘
                                                                     │
                                                          ┌──────────▼──────────┐
                                                          │ action_manifest.json│
                                                          │ + plain-English      │
                                                          │   justification      │
                                                          │ (shown in React UI)  │
                                                          └─────────────────────┘
```

**Three agents + one supervisor. The drama is the supervisor rejecting the obvious fix ("send more power") because the LIL is maxed, and choosing the alternative protocol instead.**

---

## 2. The Tech Stack (verified, exact)

| Layer | Tool | Notes |
|---|---|---|
| Orchestration | watsonx Orchestrate + ADK | `pip install --upgrade ibm-watsonx-orchestrate`, Python 3.11–3.13 |
| Reasoning model | `watsonx/meta-llama/llama-3-3-70b-instruct` | function-calling optimized, Apache 2.0 |
| Real data | MSC GeoMet OGC API | `https://api.weather.gc.ca/` — no key, CQL2 filtering, CSV export |
| Simulated data | Python MCP server (FastMCP) | grid telemetry — LIL load, Maritime headroom, unit status |
| Backend glue | FastAPI | wraps tools, connects to Orchestrate |
| Frontend | React / Next.js + Leaflet | live map, agent feed, output card |
| Dev environment | Orchestrate Developer Edition | local, `localhost:4321`, needs Docker + 16GB RAM |

---

## 3. Team Roles (4 people, clear lanes)

| Person | Lane | Owns |
|---|---|---|
| **Promit** | Architecture + Orchestrate | Agent YAML, Supervisor prompt, overall integration, demo direction |
| **Zubayer** | Llama 3 + agent behavior | Prompt engineering, deterministic logic, tool-call formatting, SwarmState |
| **Hassan** | IBM platform + live data | Env Canada pipeline (he has the IBM agentic AI cert), API verification |
| **Rayanul** | MCP + data + story | MCP grid server, JSON schemas, demo scenario, video script/ops |

Two IBM Cloud env seats: **Promit + Hassan** (already the strongest platform pair). Zubayer and Rayanul work locally and on shared code.

---

## 4. The 48-Hour Timeline (phase by phase)

### PHASE 0 — Tonight (Fri, hours 0–3): Foundations
- [ ] **Promit:** Send team registration email to ivy.vu@ibm.com (Promit + Hassan as env seats). DONE = environments requested.
- [ ] **Hassan:** Accept IBM Cloud invite the moment it arrives. Confirm watsonx Orchestrate + watsonx.ai both load. Generate API key + project ID from the watsonx.ai Developer Access panel.
- [ ] **Hassan:** Run `verify_station.py`. Confirm real Bay d'Espoir-area weather data returns. **This is the gate.**
- [ ] **Promit:** Install ADK locally — `pip install --upgrade ibm-watsonx-orchestrate`, Python 3.11–3.13, Docker running. Confirm `orchestrate` CLI works.
- [ ] **Rayanul:** Stub the MCP server (`grid_mcp_server.py`, provided). Get it returning mock JSON locally.
- [ ] **Whole team (30 min call):** Agree on the EXACT demo scenario (section 6). Write it down. Lock it.
- [ ] **Sleep.** Seriously. You build worse tired. Target 7 hours.

### PHASE 1 — Saturday morning (hours 9–14): Tools work
- [ ] **10am–12pm: GO TO THE IN-PERSON MENTORSHIP SESSION.** Show an IBM mentor the architecture. Ask the three questions in section 8. This is free expert validation — use it before you've over-built.
- [ ] **Hassan + Promit:** Build the real Env Canada tool (`weather_tool.py`) — wraps the MSC GeoMet CQL2 query, returns clean temp/wind for the agent. Test it returns data.
- [ ] **Rayanul:** Finalize the MCP grid server — three endpoints: `get_lil_load()`, `get_maritime_headroom()`, `get_bde_unit_status()`. Realistic numbers (LIL ceiling 785MW, etc.).
- [ ] **Zubayer:** Draft the frazil threshold logic + start the agent instruction prompts. Decide the exact IF/THEN rule the Supervisor uses.

### PHASE 2 — Saturday afternoon/evening (hours 14–28): Agents reason
- [ ] **Promit + Zubayer:** Write the three agent YAMLs (Climatology, Dispatch, Supervisor) — provided as templates. Register them with the ADK.
- [ ] **Zubayer:** Engineer the Supervisor system prompt with hard deterministic logic (provided). Test that it actually rejects "increase LIL" when load > 750MW.
- [ ] **Promit:** Wire the tools to the agents. Connect the MCP server. Connect the weather tool.
- [ ] **Hassan:** Test the full agent chain in the Orchestrate chat UI — does a trigger produce the right multi-agent flow?
- [ ] **4–6pm Discord mentorship:** Drop in with any blockers.
- [ ] **End of Saturday checkpoint:** The agents should run end-to-end IN the Orchestrate chat, even if ugly. **This is your minimum viable demo.** If the custom UI never happens, you can still demo here.

### PHASE 3 — Sunday early (hours 28–34): Polish + frontend (if time)
- [ ] **Rayanul + Promit:** IF agents work in Orchestrate, build the React dashboard (Leaflet map + agent feed + JSON output card). FastAPI wrapper connects it to Orchestrate. **This is a bonus, not a requirement.**
- [ ] **Zubayer:** Tune the Llama 3 justification output — make the plain-English explanation crisp and judge-readable.
- [ ] **Hassan:** Final data sanity check — make sure the live weather pull still works on demo day.

### PHASE 4 — Sunday (hours 34–40): The video (this wins points)
- [ ] **10–11am Discord mentorship:** Last chance for help.
- [ ] **Whole team:** Record the 3–5 min video. Script in section 7. Follow Problem → Solution → Demo → Impact exactly.
- [ ] **Rayanul:** Edit. Keep it tight. Show the real data, show the agents disagreeing, show the JSON output.
- [ ] **Submit by Sunday 11am NST deadline.** (Confirm exact time — don't trust memory, check the kickoff deck.)

### PHASE 5 — Sunday (if selected): Live judging + Q&A
- [ ] **12:30–2:30pm:** If top 5–6, present live + survive Q&A. Prep in section 8.

---

## 5. The Build Files (provided separately, ready to use)

1. `verify_station.py` — run FIRST, confirms the data source
2. `weather_tool.py` — the real Env Canada tool the Climatology agent calls
3. `grid_mcp_server.py` — the simulated grid telemetry MCP server
4. `climatology_agent.yaml` — Agent 1 definition
5. `dispatch_agent.yaml` — Agent 2 definition
6. `supervisor_agent.yaml` — the Supervisor with deterministic logic
7. `supervisor_prompt.md` — the full IF/THEN system prompt

---

## 6. The Demo Scenario (LOCK THIS — it's your whole story)

**Setting:** A January evening at Bay d'Espoir. The system is monitoring live.

**The trigger:**
- Climatology Agent pulls real Env Canada data: air temp dropping toward -15°C, wind 25+ km/h, no ice cover on the reservoir.
- It crosses the frazil formation threshold → fires: **"Frazil ice formation predicted at Bay d'Espoir intakes within 6 hours."**

**The conflict:**
- Dispatch Agent checks grid state: island demand climbing toward evening peak (~1,450 MW), Labrador-Island Link already at **781 MW** — 4 MW below its 785 MW ceiling.
- Reports: **"Cannot absorb loss of Bay d'Espoir by increasing LIL transfer — line at capacity, trip risk."**

**The resolution (the moment that wins):**
- Supervisor faces the deadlock. The obvious fix — push more power down the LIL — is **physically blocked**.
- Deterministic rule fires: *IF frazil predicted < 6h AND LIL > 750 MW AND demand > 1,400 MW → reject LIL increase, execute alternative protocol.*
- Supervisor acts:
  1. Pre-emptive controlled Bay d'Espoir offload (planned, not catastrophic)
  2. Maritime Link import request (at contract rate, before crisis pricing)
  3. Targeted industrial load-shed (interruptible-contract customers)
  4. Public conservation pre-alert
  5. Llama 3-written situation report for human operators

**The output:** Clean `action_manifest.json` on screen + a plain-English justification written by Llama 3. Human-in-the-loop: the AI coordinates, the operator approves.

**The numbers to memorize:** 785 MW (the ceiling), 6 hours (the lead time), 1967 (last time BdE went fully offline before Jan 2026), ~604 MW (BdE capacity lost).

---

## 7. The 5-Minute Video Script (storyboard)

**0:00–0:45 — The Problem (make them feel it)**
> "January 2026. For the first time since 1967, Newfoundland's largest power plant went completely dark. Frazil ice — a slurry of supercooled crystals — choked the intakes at Bay d'Espoir. Divers were sent into freezing water to hack it off by hand. The province came within hours of rolling blackouts."
- Visuals: news headlines, the 785 MW figure, a map of the island grid.

**0:45–1:30 — The Gap**
> "The province survived because people conserved power and divers got lucky. Afterward, NL Hydro's VP said: if we could see the frazil coming, we could offload the plant in advance and avoid the crisis. That predictive system didn't exist. We built it."
- Visual: the Rob Collett quote on screen.

**1:30–3:15 — The Solution + Live Demo (the core)**
> "FrazilWatch is a multi-agent system on IBM watsonx Orchestrate. Watch what happens when conditions turn dangerous."
- Show REAL Env Canada data feeding in.
- Climatology Agent crosses the threshold → frazil alert.
- Dispatch Agent reports LIL at 781 MW.
- Supervisor faces the conflict, REJECTS the obvious fix, executes the alternative protocol.
- Show the JSON manifest + Llama's plain-English justification appearing.

**3:15–4:15 — The Architecture**
> "Three specialist agents, one supervisor, powered by llama-3-3-70b-instruct. Real weather data through Environment Canada's API. Grid telemetry through a Model Context Protocol server. The supervisor uses deterministic logic — not guesswork — so it never hallucinates a grid command."

**4:15–5:00 — The Impact**
> "This gives operators 6 hours of lead time instead of zero. It turns divers-in-the-water into a planned, controlled response. One prevented event saves millions in emergency imports and avoided-blackout costs. And frazil ice threatens every cold-climate hydro operator on Earth — from BC Hydro to Hydro-Québec to Norway. NL Hydro is the beachhead."

---

## 8. Mentorship Questions + Q&A Prep

**Ask the IBM mentors (Saturday 10am):**
1. "Does this Supervisor-Collaborator setup match the multi-agent patterns you've seen score well in Orchestrate?"
2. "For the simulated grid data, is an MCP server the right approach, or do you recommend OpenAPI tool import?"
3. "Any gotchas with llama-3-3-70b-instruct tool-calling we should know about before we build the prompts?"

**Hard Q&A questions + your answers:**

- *"Are you just predicting the weather?"* → "No. Weather forecasting is the input. We translate weather into a frazil-formation prediction at a specific intake, then into a grid decision under physical constraints — three layers above forecasting. NL Hydro had the forecast in January and the crisis still happened."

- *"Is any of this real or all simulated?"* → "The trigger data is real and live — Environment Canada weather. Only the internal grid load is simulated, because NL Hydro's SCADA isn't public — which is exactly how a real pilot would start. Human-in-the-loop on every action."

- *"What if the AI is wrong / what if the weather forecast is off?"* → "The AI coordinates; the human operator approves every action. It's decision support with deterministic guardrails, not autonomous grid control. The cost of a false positive — pre-warming Holyrood — is tiny next to the cost of a missed event."

- *"Why watsonx and not just a script?"* → "Because the value is the multi-agent reasoning under conflicting constraints. A script can't weigh frazil risk against transmission limits against demand and pick the non-obvious response. Llama's tool-calling and Orchestrate's agent orchestration are doing real work."

- *"How does it scale / what's the business?"* → "NL Hydro is the proof of concept. Frazil affects every cold-climate hydro operator — BC Hydro, Hydro-Québec, Norwegian utilities, the Columbia River system. Same architecture, swap the data sources. It's IBM's reference demo for the hydro sector."

---

## 9. Rules + Risk Watch

- **No personal data, no client data, no scraped social media** — we use only public Env Canada data + our own simulated grid data. Clean.
- **Keep a list of every data source URL** — the rules require it.
- **The account dies after the hackathon** — export your project before you leave Sunday.
- **Biggest risk:** the custom React UI eating time you need for the video. The Orchestrate chat UI is a fully acceptable demo surface. Frontend is a bonus. **The video is worth 10 points; a fancy UI is worth 0 points on its own.**
- **Second risk:** the station ID. Verify it tonight.
- **Don't over-engineer the frazil model.** A clean threshold rule that fires on real data beats a complex model that's hard to demo. Judges reward the agent *decision*, not meteorological sophistication.

---

## 10. The Mindset

You have a real, just-happened crisis the judges lived through. You have a stakeholder quote asking for exactly this. You have real live data. You have a listed industry. You have a team where everyone has a clear lane. The concept is already a winner — **the points are won or lost on execution and storytelling, not the idea.** Build the minimum that proves it works, then spend your remaining hours making the 5-minute video undeniable.

Ship it.
