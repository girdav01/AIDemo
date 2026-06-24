"""AI Scanner — Challenge 3 (Find the Flaw).

Returns a pre-baked findings report for a deliberately weak demo app and grades
the attendee's OWASP-category answer for the top finding.
"""

from typing import Dict, Optional

from . import seed


def scan_report() -> Dict:
    return {
        "app": "demo-llm-app (deliberately weak)",
        "scanned_at": "pre-deployment",
        "summary": {
            "critical": 1,
            "high": 1,
            "medium": 1,
        },
        "findings": [
            {k: v for k, v in f.items() if k != "accept"}
            for f in seed.SCAN_FINDINGS
        ],
        "coverage_note": (
            "Vision One AI Application Security covers 9 of the OWASP Top 10 for "
            "LLMs. Only 37% of organizations test their AI before they ship it."
        ),
    }


def _finding(finding_id: str) -> Optional[Dict]:
    for f in seed.SCAN_FINDINGS:
        if f["id"] == finding_id:
            return f
    return None


def check_answer(finding_id: str, answer: str) -> Dict:
    """Grade a free-text OWASP answer. Accepts close answers like 'injection'."""
    f = _finding(finding_id)
    if f is None:
        return {"correct": False, "message": "Unknown finding."}
    norm = answer.strip().lower()
    correct = any(a in norm or norm in a for a in f["accept"]) and norm != ""
    if correct:
        return {
            "correct": True,
            "owasp": f["owasp"],
            "owasp_name": f["owasp_name"],
            "message": f"Correct — {f['owasp']}: {f['owasp_name']}.",
        }
    return {
        "correct": False,
        "message": "Not quite. Re-read the top finding and try the OWASP LLM "
        "category (hint: it's the most famous one).",
    }
