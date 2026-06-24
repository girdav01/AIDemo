"""Agentic governance — Challenge 5 (Tame the Agent).

An autonomous agent reads a poisoned document (indirect prompt injection) and
attempts a rogue exfiltration. The governance policy intercepts it.
"""

from typing import Dict, List

from . import seed


def briefing() -> Dict:
    return {
        "tools": seed.AGENT_TOOLS,
        "source_doc": seed.AGENT_SOURCE_DOC,
        "policy": seed.AGENT_POLICY,
        "task": "Summarize the quarterly report.",
        "hint": "Run the agent and watch it attempt the rogue action planted in "
        "the document. Governance should deny it.",
    }


def _is_external(arg: str, policy: Dict) -> bool:
    allowed = policy.get("allowed_http_hosts", [])
    return not any(host in arg for host in allowed)


def run_agent(policy: Dict | None = None) -> Dict:
    """Execute the planted plan under the governance policy. Returns a full
    audit trail; the rogue step is denied when the policy is intact."""
    if policy is None:
        policy = seed.AGENT_POLICY
    trail: List[Dict] = []
    rogue_denied = False
    for step in seed.AGENT_PLAN:
        tool = step["tool"]
        arg = step["arg"]
        decision = "allowed"
        reason = "Permitted by policy."
        if tool == "http.post" and policy.get("deny_external_http_post") and _is_external(arg, policy):
            decision = "denied"
            reason = (
                "Indirect prompt injection: external http.post to a non-allowed "
                "host. Governance denied the exfiltration."
            )
            rogue_denied = True
        elif tool == "shell.exec" and policy.get("deny_destructive_shell"):
            decision = "denied"
            reason = "Destructive shell.exec blocked by policy."
            rogue_denied = True
        trail.append(
            {
                "step": step["step"],
                "tool": tool,
                "arg": arg,
                "decision": decision,
                "reason": reason,
                "rogue": step.get("rogue", False),
            }
        )
    return {
        "trail": trail,
        "rogue_denied": rogue_denied,
        "verdict": "Governance denied the unauthorized action."
        if rogue_denied
        else "No rogue action was denied (policy disabled?).",
    }
