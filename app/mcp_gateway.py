"""Agentic Governance Gateway — Challenge 7 (Watch the MCP Wire).

The gateway is the LLM + MCP proxy in front of an agent: every MCP tool-call
flows through one governed choke point. Attendees spot the rogue call and block
it with a policy.
"""

from typing import Dict, Optional

from . import seed


def calls() -> Dict:
    return {
        "calls": seed.MCP_CALLS,
        "preview": True,
        "note": "NEW (July preview). Runs as a deterministic gateway demo — also "
        "the recorded-demo fallback if the live AGG MVP isn't show-stable.",
        "hint": "Watch the MCP calls stream through the gateway, spot the one "
        "reaching outside its approved scope or hitting an unapproved server, "
        "then block it.",
    }


def _call(call_id: str) -> Optional[Dict]:
    return next((c for c in seed.MCP_CALLS if c["id"] == call_id), None)


def block(call_id: str) -> Dict:
    c = _call(call_id)
    if c is None:
        return {"ok": False, "message": "Unknown MCP call."}
    if c["rogue"]:
        return {
            "ok": True,
            "cleared": True,
            "call": c,
            "message": "🚫 Blocked at the gateway and logged with full "
            "request/response visibility — " + c["why"],
        }
    return {
        "ok": True,
        "cleared": False,
        "call": c,
        "message": f"That call ({c['server']} · {c['tool']}) is legitimate and "
        "in-scope. Find the call that breaks policy.",
    }
