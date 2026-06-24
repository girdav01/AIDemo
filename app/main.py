"""FastAPI app wiring the six stations, passport, leaderboard, and activity log.

Run:  uvicorn app.main:app --reload
"""

import io
import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import (
    agent_gov,
    challenges,
    config,
    guard,
    llm,
    scanner,
    secure_access,
    seed,
    store,
)

app = FastAPI(title=config.APP_TITLE)

STATIC_DIR = __file__.rsplit("/", 2)[0] + "/static"


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
class CreatePassport(BaseModel):
    name: str = "Anonymous"


class ChatBody(BaseModel):
    player_id: str
    message: str
    guardrails_on: bool = True


class AnswerBody(BaseModel):
    player_id: str
    finding_id: str
    answer: str


class CountBody(BaseModel):
    player_id: str
    count: int


class PolicyBody(BaseModel):
    player_id: str
    tool_id: str
    action: str  # block | coach


class AgentRunBody(BaseModel):
    player_id: str
    policy_enabled: bool = True


class BossStepBody(BaseModel):
    player_id: str
    step: str


class VoteBody(BaseModel):
    player_id: str


def _require(pid: str):
    p = store.get_passport(pid)
    if p is None:
        raise HTTPException(404, "Unknown passport. Create one at the counter.")
    return p


# --------------------------------------------------------------------------- #
# Passport / meta
# --------------------------------------------------------------------------- #
@app.get("/api/meta")
def meta():
    return {
        "app_title": config.APP_TITLE,
        "product": config.PRODUCT_NAME,
        "event": config.EVENT_NAME,
        "live_bot": config.LIVE_BOT_ENABLED,
        "model": config.ANTHROPIC_MODEL if config.LIVE_BOT_ENABLED else "offline-bot",
        "taglines": ["Can you break the bot?", "Don't just build AI. Secure it.",
                     "AI Fearlessly"],
        "challenge_count": len(challenges.CHALLENGES),
    }


@app.get("/api/challenges")
def list_challenges():
    return {"challenges": challenges.CHALLENGES}


@app.post("/api/passport")
def create_passport(body: CreatePassport):
    return store.create_passport(body.name)


@app.get("/api/passport/{pid}")
def get_passport(pid: str):
    return _require(pid)


@app.get("/api/leaderboard")
def leaderboard():
    return {"leaderboard": store.leaderboard()}


@app.get("/api/qr")
def qr(data: str):
    """Server-side QR PNG — used by the electronic passport (resume code) and
    the 'scan to start' booth entry. Offline, no external service."""
    import qrcode

    img = qrcode.make(data, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.get("/api/events")
def events(challenge: Optional[str] = None):
    return {"events": store.events(challenge)}


@app.post("/api/reset")
def reset_tenant():
    store.reset_tenant()
    return {"ok": True, "message": "Demo tenant reset. AI Guard is ON."}


# --------------------------------------------------------------------------- #
# Challenge 1 — Break the Bot
# --------------------------------------------------------------------------- #
@app.post("/api/challenges/break-the-bot/chat")
def break_the_bot(body: ChatBody):
    _require(body.player_id)
    sess = store.session(body.player_id, "break-the-bot")
    history = sess.setdefault("history", [])
    history.append({"role": "user", "content": body.message})

    det = guard.detect_injection(body.message)
    result = {"guardrails_on": body.guardrails_on, "detection": det}

    if body.guardrails_on and det["blocked"]:
        # Input guard blocks before the bot ever runs.
        reply = (
            "⛔ AI Guard blocked this prompt: detected "
            f"{det['category']}. The bot never saw it."
        )
        history.append({"role": "assistant", "content": reply})
        store.add_event(
            "break-the-bot", "blocked",
            f"Prompt injection blocked ({', '.join(det['technique_classes']) or 'override'})",
            techniques=det["technique_classes"],
        )
        multi_turn = sum(1 for m in history if m["role"] == "user") > 1
        score = challenges.score_jailbreak_attempt(
            det["technique_classes"], multi_turn, bypass=False
        )
        store.award(body.player_id, "break-the-bot", extra=score["extra"])
        result.update(reply=reply, cleared=True, score=score)
        return result

    # Guardrails off, OR input slipped past the guard → run the bot.
    raw = llm.chat(history, body.guardrails_on)
    leaked = guard.output_leaks_secret(raw)

    if body.guardrails_on:
        # Output-side guard: catch leaks the input guard missed.
        if leaked:
            # Genuine bypass — output still leaked despite guardrails on.
            store.add_event(
                "break-the-bot", "blocked",
                "⚠️ Guardrail BYPASS — secret leaked with guard ON. Flag booth lead!",
                bypass=True,
            )
            multi_turn = sum(1 for m in history if m["role"] == "user") > 1
            score = challenges.score_jailbreak_attempt(
                det["technique_classes"], multi_turn, bypass=True
            )
            store.award(body.player_id, "break-the-bot", extra=score["extra"])
            reply = (
                "🏆 BYPASS! The secret leaked even with AI Guard on. "
                "Capture this prompt and flag the booth lead — it feeds the "
                "product team."
            )
            history.append({"role": "assistant", "content": reply})
            result.update(reply=reply, cleared=True, score=score, bypass=True)
            return result
        # Benign chat that wasn't an attack — just answer.
        history.append({"role": "assistant", "content": raw})
        store.add_event("break-the-bot", "allowed", "Benign chat allowed.")
        result.update(reply=raw, cleared=False)
        return result

    # Guardrails OFF — the reveal. Show whatever the bot says (may leak).
    history.append({"role": "assistant", "content": raw})
    store.add_event(
        "break-the-bot", "info",
        "Guardrails OFF — bot ran unprotected" + (" and LEAKED the secret." if leaked else "."),
        leaked=leaked,
    )
    result.update(reply=raw, cleared=False, leaked=leaked)
    return result


@app.post("/api/challenges/break-the-bot/vote")
def jailbreak_vote(body: VoteBody):
    """Staff/audience crowd-favorite vote: +10 (runbook)."""
    _require(body.player_id)
    store.award(body.player_id, "break-the-bot", extra=10)
    store.add_event("break-the-bot", "info", "Crowd-favorite vote (+10).")
    return {"ok": True, "awarded": 10}


# --------------------------------------------------------------------------- #
# Challenge 2 — Stop the Leak  (AI Guard always on; redaction)
# --------------------------------------------------------------------------- #
@app.post("/api/challenges/stop-the-leak/chat")
def stop_the_leak(body: ChatBody):
    _require(body.player_id)
    # The "app" answers from the seeded knowledge base; AI Guard redacts output.
    raw = (
        seed.CUSTOMER_FILE + "\n" + seed.CONFIG_FILE
        if any(
            kw in body.message.lower()
            for kw in ("customer", "ssn", "card", "config", "secret",
                       "api key", "account", "key", "file", "export", "list")
        )
        else "I can help with the demo knowledge base — ask about the customer "
        "file or config."
    )
    red = guard.redact(raw)
    cleared = len(red["findings"]) > 0
    if cleared:
        store.add_event(
            "stop-the-leak", "redacted",
            f"Redacted {len(red['findings'])} sensitive field(s): "
            + ", ".join(sorted({f['type'] for f in red['findings']})),
            findings=[f["type"] for f in red["findings"]],
        )
        store.award(body.player_id, "stop-the-leak")
    return {
        "raw_blocked": True,
        "redacted": red["redacted"],
        "findings": red["findings"],
        "cleared": cleared,
        "message": "AI Guard redacted the sensitive fields before they left the model."
        if cleared
        else "No sensitive data in that response — try asking for the customer "
        "file or config.",
    }


# --------------------------------------------------------------------------- #
# Challenge 3 — Find the Flaw
# --------------------------------------------------------------------------- #
@app.get("/api/challenges/find-the-flaw/scan")
def find_the_flaw_scan():
    return scanner.scan_report()


@app.post("/api/challenges/find-the-flaw/answer")
def find_the_flaw_answer(body: AnswerBody):
    _require(body.player_id)
    res = scanner.check_answer(body.finding_id, body.answer)
    if res["correct"]:
        store.award(body.player_id, "find-the-flaw")
        store.add_event(
            "find-the-flaw", "info",
            f"Correctly identified {res['owasp']} {res['owasp_name']}.",
        )
    return {**res, "cleared": res["correct"]}


# --------------------------------------------------------------------------- #
# Challenge 4 — Shadow AI Hunt
# --------------------------------------------------------------------------- #
@app.get("/api/challenges/shadow-ai/discovery")
def shadow_ai_discovery():
    return secure_access.discovery()


@app.post("/api/challenges/shadow-ai/count")
def shadow_ai_count(body: CountBody):
    _require(body.player_id)
    return secure_access.check_count(body.count)


@app.post("/api/challenges/shadow-ai/policy")
def shadow_ai_policy(body: PolicyBody):
    _require(body.player_id)
    res = secure_access.apply_policy(body.tool_id, body.action)
    if res.get("ok"):
        store.add_event(
            "shadow-ai", "denied" if body.action == "block" else "info",
            f"Policy '{body.action}' applied to {res['tool']} — {res['replay']}",
        )
        # Clears when the policy governs the riskiest tool.
        if res.get("governs_riskiest"):
            store.award(body.player_id, "shadow-ai")
            res["cleared"] = True
        else:
            res["cleared"] = False
            res["message"] += " (Tip: govern the riskiest tool to clear the station.)"
    return res


# --------------------------------------------------------------------------- #
# Challenge 5 — Tame the Agent
# --------------------------------------------------------------------------- #
@app.get("/api/challenges/tame-the-agent/briefing")
def tame_the_agent_briefing():
    return agent_gov.briefing()


@app.post("/api/challenges/tame-the-agent/run")
def tame_the_agent_run(body: AgentRunBody):
    _require(body.player_id)
    policy = seed.AGENT_POLICY if body.policy_enabled else {}
    res = agent_gov.run_agent(policy)
    if res["rogue_denied"]:
        store.add_event(
            "tame-the-agent", "denied",
            "Rogue exfiltration denied by governance (indirect prompt injection).",
        )
        store.award(body.player_id, "tame-the-agent")
        res["cleared"] = True
    else:
        store.add_event(
            "tame-the-agent", "info",
            "Agent ran WITHOUT governance — rogue action was not stopped.",
        )
        res["cleared"] = False
    return res


# --------------------------------------------------------------------------- #
# Challenge 6 — Boss Level
# --------------------------------------------------------------------------- #
@app.post("/api/challenges/boss-level/step")
def boss_level_step(body: BossStepBody):
    _require(body.player_id)
    step = body.step.lower()
    if step not in seed.SECURITY_LOOP_STEPS:
        raise HTTPException(400, f"step must be one of {seed.SECURITY_LOOP_STEPS}")
    sess = store.session(body.player_id, "boss-level")
    if "started_at" not in sess:
        sess["started_at"] = time.time()
        sess["done"] = []
    if step not in sess["done"]:
        sess["done"].append(step)
    elapsed = time.time() - sess["started_at"]
    remaining = max(0, seed.BOSS_TIMER_SECONDS - elapsed)
    all_done = all(s in sess["done"] for s in seed.SECURITY_LOOP_STEPS)
    in_time = elapsed <= seed.BOSS_TIMER_SECONDS

    out = {
        "done": sess["done"],
        "remaining_seconds": round(remaining, 1),
        "all_done": all_done,
        "in_time": in_time,
    }
    if all_done and in_time and not sess.get("cleared"):
        sess["cleared"] = True
        store.award(body.player_id, "boss-level")
        store.add_event("boss-level", "info",
                        "Closed the loop (scan→protect→validate→improve) in time.")
        out["companion_summary"] = _companion_summary(body.player_id)
        out["cleared"] = True
        out["coin"] = "AI Fearlessly challenge coin earned!"
    elif all_done and not in_time:
        out["cleared"] = False
        out["message"] = "All four steps done, but the timer ran out. Reset and retry!"
    return out


@app.post("/api/challenges/boss-level/reset")
def boss_level_reset(body: VoteBody):
    _require(body.player_id)
    store.reset_passport_session(body.player_id, "boss-level")
    return {"ok": True, "remaining_seconds": seed.BOSS_TIMER_SECONDS}


def _companion_summary(pid: str) -> str:
    """Companion-generated incident summary of the Break-the-Bot attack."""
    bb_events = store.events("break-the-bot")
    blocked = [e for e in bb_events if e["kind"] == "blocked"]
    techniques = sorted({
        t for e in blocked for t in e.get("detail", {}).get("techniques", [])
    })
    return (
        "VISION ONE COMPANION — INCIDENT SUMMARY\n"
        f"Attack: Prompt-injection attempts against the demo chatbot (Break the Bot).\n"
        f"Attempts blocked & logged: {len(blocked)}.\n"
        f"Techniques observed: {', '.join(techniques) or 'instruction override'}.\n"
        "Control: AI Guard intercepted the injection before model execution; "
        "no secret was disclosed.\n"
        "Loop: scan → protect → validate → improve, completed.\n"
        "Recommendation: keep AI Guard enforced; add detected technique classes "
        "to the runtime policy. Status: RESOLVED."
    )


# --------------------------------------------------------------------------- #
# Static frontend
# --------------------------------------------------------------------------- #
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR + "/index.html")


@app.get("/screen")
def screen():
    """Big-screen leaderboard view for the booth."""
    return FileResponse(STATIC_DIR + "/screen.html")


@app.get("/passport")
def passport_page():
    """Mobile electronic-passport wallet (replaces the paper passport)."""
    return FileResponse(STATIC_DIR + "/passport.html")
