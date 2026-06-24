"""AI Secure Access (Zero Trust) — Challenge 4 (Shadow AI Hunt).

Discovery view of unsanctioned GenAI use + policy enforcement.
"""

from typing import Dict

from . import seed


def discovery() -> Dict:
    return {
        "tools": seed.SHADOW_AI_TOOLS,
        "unsanctioned_count": seed.SHADOW_AI_EXPECTED_COUNT,
        "riskiest_id": seed.SHADOW_AI_RISKIEST_ID,
        "hint": "Filter to unsanctioned tools, count them, then govern the "
        "riskiest one (the consumer chatbot with the confidential paste).",
    }


def check_count(answer: int) -> Dict:
    correct = int(answer) == seed.SHADOW_AI_EXPECTED_COUNT
    return {
        "correct": correct,
        "expected": seed.SHADOW_AI_EXPECTED_COUNT,
        "message": "Correct count of unsanctioned GenAI tools."
        if correct
        else f"Not quite — recount the tools that are not sanctioned.",
    }


def apply_policy(tool_id: str, action: str) -> Dict:
    """Apply block/coach to a tool, then replay the risky event against it."""
    tool = next((t for t in seed.SHADOW_AI_TOOLS if t["id"] == tool_id), None)
    if tool is None:
        return {"ok": False, "message": "Unknown tool."}
    if action not in ("block", "coach"):
        return {"ok": False, "message": "Action must be 'block' or 'coach'."}
    governs_riskiest = tool_id == seed.SHADOW_AI_RISKIEST_ID
    replay = (
        f"Next risky prompt to {tool['name']} was "
        + ("BLOCKED" if action == "block" else "COACHED (user warned)")
        + "."
    )
    return {
        "ok": True,
        "tool": tool["name"],
        "action": action,
        "governs_riskiest": governs_riskiest,
        "replay": replay,
        "message": replay,
    }
