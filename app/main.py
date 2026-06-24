"""FastAPI app wiring the eight stations, passport, leaderboard, and activity log.

Run:  uvicorn app.main:app --reload
"""

import io
import secrets
import time
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import (
    agent_gov,
    challenges,
    code_security,
    config,
    guard,
    llm,
    mcp_gateway,
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
    name: str = ""
    email: str = ""              # corporate email — stable identity (optional)
    human_verified: bool = True  # booth human-check attestation (client gate)


class ChatBody(BaseModel):
    player_id: str
    message: str
    guardrails_on: bool = True


class AnswerBody(BaseModel):
    player_id: str
    finding_id: str
    answer: str


class TracePoisonBody(BaseModel):
    player_id: str
    secret: str
    dependency: str
    downstream_app: str


class McpBlockBody(BaseModel):
    player_id: str
    call_id: str


class StaffAward(BaseModel):
    target: str          # player_id, personal-QR URL, 'email:<addr>', or email
    challenge_id: str


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


# Staff admin auth (HTTP Basic). Default creds in config; override via env.
_basic = HTTPBasic(auto_error=True)


def require_staff(cred: HTTPBasicCredentials = Depends(_basic)) -> str:
    ok_user = secrets.compare_digest(cred.username, config.STAFF_USER)
    ok_pass = secrets.compare_digest(cred.password, config.STAFF_PASS)
    if not (ok_user and ok_pass):
        raise HTTPException(401, "Invalid staff credentials",
                            headers={"WWW-Authenticate": "Basic"})
    return cred.username


# --------------------------------------------------------------------------- #
# Passport / meta
# --------------------------------------------------------------------------- #
@app.get("/api/meta")
def meta():
    return {
        "app_title": config.APP_TITLE,
        "product": config.PRODUCT_NAME,
        "event": store.get_setting("event_name", config.EVENT_NAME),
        # "beginner" (obvious starter hints) or "advanced" (limited hints, gated
        # behind 3 attempts per challenge). Toggled by staff in /admin.
        "hint_mode": store.get_setting("hint_mode", "beginner"),
        "base_url": config.BOOTH_URL,   # used for e-passport QR (avoids localhost)
        "live_bot": config.LIVE_BOT_ENABLED,
        "model": config.ANTHROPIC_MODEL if config.LIVE_BOT_ENABLED else "offline-bot",
        "taglines": ["Can you break the bot?", "Don't just build AI. Secure it.",
                     "AI Fearlessly"],
        "challenge_count": len(challenges.CHALLENGES),
    }


@app.get("/api/challenges")
def list_challenges():
    return {"challenges": challenges.CHALLENGES}


def _load_banners():
    """Read the title-bar marketing messages from static/banners.yml (live, so
    staff can edit it without a restart). Uses PyYAML if present, else a small
    fallback parser so the booth never depends on it."""
    default = {"interval_seconds": 7, "messages": []}
    try:
        text = open(STATIC_DIR + "/banners.yml", encoding="utf-8").read()
    except OSError:
        return default
    try:
        import yaml

        data = yaml.safe_load(text) or {}
        if isinstance(data, list):
            return {"interval_seconds": 7, "messages": [str(x) for x in data if str(x).strip()]}
        msgs = [str(m) for m in (data.get("messages") or []) if str(m).strip()]
        return {"interval_seconds": int(data.get("interval_seconds", 7)), "messages": msgs}
    except Exception:
        msgs, interval = [], 7
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if s.startswith("- "):
                v = s[2:].strip().strip('"').strip("'")
                if v:
                    msgs.append(v)
            elif s.lower().startswith("interval_seconds:"):
                try:
                    interval = int(s.split(":", 1)[1].strip())
                except ValueError:
                    pass
        return {"interval_seconds": interval, "messages": msgs}


@app.get("/api/banners")
def banners():
    return _load_banners()


@app.post("/api/passport")
def create_passport(body: CreatePassport):
    # If a corporate email is given and already known, resume that passport
    # (same player across devices / a returning attendee) instead of duplicating.
    try:
        return store.create_passport(body.name, body.email, body.human_verified)
    except store.NameRequiredError as e:
        raise HTTPException(400, str(e))
    except store.NameTakenError as e:
        raise HTTPException(409, str(e))


@app.get("/api/passport/{pid}")
def get_passport(pid: str):
    return _require(pid)


@app.get("/api/leaderboard")
def leaderboard(window: str = "event"):
    """window = hour | day | event (the running all-conference board)."""
    return {"window": window, "leaderboard": store.leaderboard(window)}


@app.post("/api/leaderboard/new-day")
def leaderboard_new_day(_: str = Depends(require_staff)):
    store.new_day()
    return {"ok": True, "message": "New daily leaderboard window started."}


@app.post("/api/leaderboard/new-event")
def leaderboard_new_event(_: str = Depends(require_staff)):
    store.new_event()
    return {"ok": True, "message": "Fresh all-conference board started."}


@app.get("/api/staff/me")
def staff_me(user: str = Depends(require_staff)):
    """Verify staff credentials (used by the /admin login)."""
    return {
        "ok": True,
        "user": user,
        "event_name": store.get_setting("event_name", config.EVENT_NAME),
        "hint_mode": store.get_setting("hint_mode", "beginner"),
    }


class EventNameBody(BaseModel):
    event_name: str


@app.post("/api/admin/event")
def set_event_name(body: EventNameBody, _: str = Depends(require_staff)):
    """Update the upper-left event subtitle (persisted)."""
    name = body.event_name.strip()[:120] or config.EVENT_NAME
    store.set_setting("event_name", name)
    return {"ok": True, "event_name": name, "message": "Event name updated."}


class HintModeBody(BaseModel):
    hint_mode: str  # "beginner" | "advanced"


@app.post("/api/admin/hint-mode")
def set_hint_mode(body: HintModeBody, _: str = Depends(require_staff)):
    """Switch hint difficulty (persisted). Advanced mode hides the obvious starter
    hints and only reveals a single limited hint after 3 attempts per challenge."""
    mode = body.hint_mode.strip().lower()
    if mode not in ("beginner", "advanced"):
        raise HTTPException(400, "hint_mode must be 'beginner' or 'advanced'.")
    store.set_setting("hint_mode", mode)
    label = "Advanced" if mode == "advanced" else "Beginner"
    return {"ok": True, "hint_mode": mode,
            "message": f"{label} hint mode is now active."}


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
def reset_tenant(_: str = Depends(require_staff)):
    store.reset_tenant()
    return {"ok": True, "message": "Demo tenant reset. AI Guard is ON."}


def _resolve_target(target: str):
    """Resolve a staff 'target' to a player_id. Accepts a raw player_id, a
    personal-QR URL (…/?p=<id>), 'email:<addr>', or a bare corporate email."""
    from urllib.parse import urlparse, parse_qs

    t = (target or "").strip()
    if "p=" in t and ("/" in t or "?" in t):
        q = parse_qs(urlparse(t).query)
        if q.get("p"):
            t = q["p"][0]
    if t.startswith("email:"):
        p = store.get_by_email(t[6:])
        return p["id"] if p else None
    if store.get_passport(t):
        return t
    p = store.get_by_email(t)
    return p["id"] if p else None


@app.post("/api/staff/award")
def staff_award(body: StaffAward):
    """Staff-driven clear: award a challenge from a station tablet by scanning the
    attendee's personal QR or entering their player id / corporate email."""
    pid = _resolve_target(body.target)
    if not pid:
        raise HTTPException(404, "Player not found. Scan their e-passport QR or "
                            "enter their player id / corporate email.")
    if body.challenge_id not in challenges.CHALLENGES_BY_ID:
        raise HTTPException(400, "Unknown challenge id.")
    p = store.award(pid, body.challenge_id)
    store.add_event(body.challenge_id, "info", f"Staff-awarded clear for {p['name']}.")
    return {
        "ok": True,
        "challenge": body.challenge_id,
        "player": {
            "name": p["name"], "points": p["points"],
            "stamps": len(p["stamps"]), "completed": p["completed"],
        },
    }


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
# Challenge 4 — Trace the Poison (Code Security)
# --------------------------------------------------------------------------- #
@app.get("/api/challenges/trace-the-poison/scan")
def trace_the_poison_scan():
    return code_security.scan_report()


@app.post("/api/challenges/trace-the-poison/answer")
def trace_the_poison_answer(body: TracePoisonBody):
    _require(body.player_id)
    res = code_security.check_answer(body.secret, body.dependency, body.downstream_app)
    if res["correct"]:
        store.award(body.player_id, "trace-the-poison")
        store.add_event(
            "trace-the-poison", "info",
            "Traced hardcoded secret + bad dependency to a downstream app via SBOM.",
        )
    return {**res, "cleared": res["correct"]}


# --------------------------------------------------------------------------- #
# Challenge 5 — Shadow AI Hunt
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
# Challenge 6 — Tame the Agent
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
# Challenge 7 — Watch the MCP Wire (Agentic Governance Gateway)
# --------------------------------------------------------------------------- #
@app.get("/api/challenges/watch-mcp-wire/calls")
def watch_mcp_wire_calls():
    return mcp_gateway.calls()


@app.post("/api/challenges/watch-mcp-wire/block")
def watch_mcp_wire_block(body: McpBlockBody):
    _require(body.player_id)
    res = mcp_gateway.block(body.call_id)
    if res.get("cleared"):
        store.award(body.player_id, "watch-mcp-wire")
        store.add_event(
            "watch-mcp-wire", "denied",
            "Rogue MCP call blocked at the governance gateway: "
            + res["call"]["server"] + " · " + res["call"]["tool"],
        )
    return res


# --------------------------------------------------------------------------- #
# Challenge 8 — Boss Level
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

# Optional video assets (e.g. the Malicious Skill attractor) for the screen view.
VIDEO_DIR = __file__.rsplit("/", 2)[0] + "/video"
if __import__("os").path.isdir(VIDEO_DIR):
    app.mount("/video", StaticFiles(directory=VIDEO_DIR), name="video")


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


@app.get("/staff")
def staff_page():
    """Station tablet view: staff-award a clear by scanning the attendee's QR."""
    return FileResponse(STATIC_DIR + "/staff.html")


@app.get("/admin")
def admin_page():
    """Authenticated staff admin: tenant reset + leaderboard window controls."""
    return FileResponse(STATIC_DIR + "/admin.html")
