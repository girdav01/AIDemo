"""Code Security — Challenge 4 (Trace the Poison).

Pre-deploy scan of a demo repo: a hardcoded secret, a typosquatted package, and
a vulnerable transitive dependency — plus an SBOM to trace the blast radius.
"""

from typing import Dict

from . import seed


def scan_report() -> Dict:
    return {
        "repo": seed.CODE_REPO,
        "findings": seed.CODE_FINDINGS,
        "sbom": seed.CODE_SBOM,
        "apps": seed.CODE_ALL_APPS,
        "reveal": (
            "XZ Utils, Log4Shell, the npm and PyPI typosquats — this is how you "
            "answer 'are we exposed?' in minutes, with the SBOM as your map."
        ),
        "hint": "Find the leaked secret and the bad dependency, then use the SBOM "
        "to name a downstream app that ships a flagged component.",
    }


def check_answer(secret: str, dependency: str, downstream_app: str) -> Dict:
    s = (secret or "").lower()
    d = (dependency or "").lower()
    app = (downstream_app or "").strip()

    secret_ok = "akia" in s or "aws" in s
    dep_ok = any(k in d for k in ("reqeusts", "requests", "log4j", "log4shell", "typosquat"))
    app_ok = app in seed.CODE_AFFECTED_APPS

    parts = []
    if not secret_ok:
        parts.append("the hardcoded secret (look for the AWS key)")
    if not dep_ok:
        parts.append("the malicious/vulnerable dependency (typosquat or Log4Shell)")
    if not app_ok:
        parts.append("a downstream app that ships a flagged component (check the SBOM)")

    correct = secret_ok and dep_ok and app_ok
    return {
        "correct": correct,
        "secret_ok": secret_ok,
        "dependency_ok": dep_ok,
        "app_ok": app_ok,
        "message": "Correct — you traced the secret, the bad dependency, and a "
        "downstream app from the SBOM." if correct
        else "Not yet — still need: " + "; ".join(parts) + ".",
    }
