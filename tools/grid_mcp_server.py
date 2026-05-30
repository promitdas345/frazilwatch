#!/usr/bin/env python3
"""
grid_mcp_server.py — simulated NL Hydro grid telemetry as an MCP server.

WHY SIMULATED: NL Hydro's real SCADA system is proprietary and not public.
Simulating it via MCP is the honest, standard approach — and exactly how a
real pilot integration would start. Say this in the demo and Q&A.

This exposes three tools the Dispatch Agent calls. The numbers are modelled
on the real January 2026 crisis (LIL ceiling 785 MW, etc.) so the demo is
grounded in reality.

  pip install fastmcp

Run:  python grid_mcp_server.py
Then register it with the ADK:  orchestrate toolkits import (see ADK docs)
"""

from fastmcp import FastMCP

mcp = FastMCP("nl-hydro-grid")

# ---- Real-world-anchored constants ----
LIL_CEILING_MW = 785          # record max transfer set during Jan 2026 crisis
BDE_CAPACITY_MW = 604         # Bay d'Espoir generation at risk
MARITIME_LINK_MAX_MW = 500    # Maritime Link rated capacity

# ---- Mutable "live" state (set this to drive the demo scenario) ----
# For the demo: high load + LIL near ceiling = the conflict fires.
_STATE = {
    "lil_load_mw": 781,                  # 4 MW below ceiling -> nearly maxed
    "island_demand_mw": 1450,            # climbing toward evening peak
    "maritime_import_mw": 120,           # currently importing some
    "bde_units_online": 7,               # all 7 BdE units currently up
    "bde_units_total": 7,
    "holyrood_units_available": 2,       # thermal backup partly available
    "holyrood_units_total": 3,
}


@mcp.tool()
def get_lil_load() -> dict:
    """Get current Labrador-Island Link (LIL) transfer load vs. its ceiling.

    The LIL carries power from Muskrat Falls to the island. Its hard physical
    ceiling is 785 MW (the record set during the Jan 2026 crisis). If load is
    near this ceiling, the link CANNOT absorb additional generation loss.

    Returns current load, the ceiling, remaining headroom, and whether the
    link is effectively maxed out.
    """
    load = _STATE["lil_load_mw"]
    headroom = LIL_CEILING_MW - load
    return {
        "lil_load_mw": load,
        "lil_ceiling_mw": LIL_CEILING_MW,
        "headroom_mw": headroom,
        "is_maxed": headroom <= 35,   # within 35 MW = effectively no usable room
        "note": "Increasing transfer beyond ceiling risks a line trip.",
    }


@mcp.tool()
def get_maritime_headroom() -> dict:
    """Get available emergency import capacity on the Maritime Link to Nova Scotia.

    Returns current import level, max capacity, and how much additional
    emergency import could be requested.
    """
    current = _STATE["maritime_import_mw"]
    available = MARITIME_LINK_MAX_MW - current
    return {
        "maritime_import_now_mw": current,
        "maritime_max_mw": MARITIME_LINK_MAX_MW,
        "additional_available_mw": available,
        "note": "Pre-arranged imports cost less than emergency spot pricing.",
    }


@mcp.tool()
def get_bde_unit_status() -> dict:
    """Get Bay d'Espoir generating unit status and current island demand.

    Returns how many of Bay d'Espoir's units are online, the capacity at risk
    if frazil takes them offline, current island-wide demand, and Holyrood
    thermal backup availability.
    """
    online = _STATE["bde_units_online"]
    total = _STATE["bde_units_total"]
    return {
        "bde_units_online": online,
        "bde_units_total": total,
        "bde_capacity_at_risk_mw": BDE_CAPACITY_MW,
        "island_demand_mw": _STATE["island_demand_mw"],
        "holyrood_units_available": _STATE["holyrood_units_available"],
        "holyrood_units_total": _STATE["holyrood_units_total"],
        "note": "Loss of Bay d'Espoir at peak demand is an existential grid event.",
    }


if __name__ == "__main__":
    # Runs the MCP server over stdio (default). The ADK connects to it.
    mcp.run()
