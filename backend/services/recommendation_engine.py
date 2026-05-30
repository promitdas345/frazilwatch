def get_recommendations(risk: dict, weather: dict, marine: dict) -> dict:
    level = risk.get("risk_level", "LOW")
    grid = risk.get("grid_state", {})
    lil_maxed = grid.get("lil_is_maxed", False)
    demand = grid.get("island_demand_mw", 0)
    lil_load = grid.get("lil_load_mw", 0)
    lil_ceil = grid.get("lil_ceiling_mw", 785)
    maritime = grid.get("maritime_headroom_mw", 380)

    if level == "LOW":
        return {
            "action_required": False,
            "protocol": "MONITOR",
            "priority": "LOW",
            "obvious_fix_blocked": False,
            "actions": [
                {
                    "id": "monitor",
                    "action": "Continue standard monitoring",
                    "detail": "No immediate risk. Hourly weather checks, routine intake inspection.",
                    "urgency": "routine",
                },
            ],
            "summary": "No frazil risk detected. Standard monitoring in effect.",
        }

    if level == "ELEVATED":
        return {
            "action_required": True,
            "protocol": "ELEVATED_WATCH",
            "priority": "MEDIUM",
            "obvious_fix_blocked": False,
            "actions": [
                {
                    "id": "increase_monitoring",
                    "action": "Increase monitoring to 15-minute checks",
                    "detail": "Alert on-call operator. Conditions approaching threshold.",
                    "urgency": "soon",
                },
                {
                    "id": "prep_equipment",
                    "action": "Pre-position intake clearing equipment",
                    "detail": "Verify compressed air systems are operational at all intakes.",
                    "urgency": "soon",
                },
            ],
            "summary": "Elevated frazil risk. Prepare response — conditions approaching threshold.",
        }

    # HIGH — apply the deterministic decision rule
    blocked = lil_maxed and demand > 1400

    if blocked:
        actions = [
            {
                "id": "preemptive_offload",
                "action": "Pre-emptive controlled Bay d'Espoir offload",
                "detail": "Initiate planned ramp-down of BdE units. Gradual — NOT a sudden trip.",
                "urgency": "immediate",
            },
            {
                "id": "maritime_import",
                "action": f"Request Maritime Link emergency import (~{maritime} MW available)",
                "detail": "Secure power from Nova Scotia at contract rate before spot pricing.",
                "urgency": "immediate",
            },
            {
                "id": "industrial_loadshed",
                "action": "Targeted industrial load-shed",
                "detail": "Curtail interruptible-contract industrial customers only. Not residential.",
                "urgency": "immediate",
            },
            {
                "id": "conservation_alert",
                "action": "Issue public conservation pre-alert",
                "detail": "Measured advisory ahead of evening peak demand.",
                "urgency": "within_1hr",
            },
            {
                "id": "operator_report",
                "action": "Generate operator situation report",
                "detail": "Full data packet for human operator approval.",
                "urgency": "immediate",
            },
        ]
        return {
            "action_required": True,
            "protocol": "ALTERNATIVE_RESPONSE",
            "priority": "CRITICAL",
            "obvious_fix": "increase_LIL_transfer",
            "obvious_fix_blocked": True,
            "blocked_reason": (
                f"Labrador-Island Link at {lil_load}/{lil_ceil} MW — "
                f"only {lil_ceil - lil_load} MW headroom. Trip risk if exceeded."
            ),
            "actions": actions,
            "human_approval_required": True,
            "approval_text": "Approve pre-emptive Bay d'Espoir offload and Maritime Link import request.",
            "summary": (
                f"HIGH frazil risk. LIL maxed at {lil_load}/{lil_ceil} MW — "
                "obvious fix blocked. Alternative response protocol activated."
            ),
        }

    return {
        "action_required": True,
        "protocol": "STANDARD_RESPONSE",
        "priority": "HIGH",
        "obvious_fix": "increase_LIL_transfer",
        "obvious_fix_blocked": False,
        "actions": [
            {
                "id": "increase_lil",
                "action": "Pre-arrange increased LIL transfer",
                "detail": f"LIL has headroom — arrange additional Muskrat Falls import.",
                "urgency": "immediate",
            },
            {
                "id": "preemptive_offload",
                "action": "Stage controlled Bay d'Espoir offload",
                "detail": "Prepare ramp-down in case frazil worsens.",
                "urgency": "within_1hr",
            },
        ],
        "human_approval_required": True,
        "approval_text": "Approve pre-emptive LIL increase and staged BdE offload preparation.",
        "summary": "HIGH frazil risk. Grid has headroom — standard response available.",
    }
