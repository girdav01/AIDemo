"""In-memory state: passports, the activity/blocked-event log, and the
leaderboard. Single shared demo tenant.

Points are recorded in a timestamped ledger so the leaderboard can be shown over
a time window — **this hour**, **today**, or the whole **event** (the running
all-conference board). Clock windows use the server's local time, so set the
booth machine to the event's timezone (America/Los_Angeles for Las Vegas).
"""

import json
import os
import sqlite3
import threading
import time
import uuid
from typing import Dict, List, Optional

from .challenges import LAYER_BY_ID, LAYERS

# Optional SQLite persistence so a restart doesn't wipe the board.
# Opt-in (run.sh sets BOOTH_PERSIST=1); off by default so dev/tests stay in-memory.
_PERSIST = os.environ.get("BOOTH_PERSIST") == "1"
_DB_PATH = os.environ.get("BOOTH_DB", "booth_state.db")


class NameTakenError(Exception):
    """Raised when an explicit screen name is already in use (no email given)."""


class NameRequiredError(Exception):
    """Raised when no name is given — anonymous players are not allowed."""

# challenge_id -> base points awarded for a clear (stamp value)
CLEAR_POINTS = {
    "break-the-bot": 10,      # base; jailbreak-wall bonuses add on top
    "stop-the-leak": 50,
    "find-the-flaw": 50,
    "trace-the-poison": 75,
    "shadow-ai": 50,
    "tame-the-agent": 50,
    "watch-mcp-wire": 75,
    "boss-level": 100,
}
FULL_PASSPORT_BONUS = 100  # awarded once one challenge in each layer is cleared

WINDOWS = ("hour", "day", "event")

_lock = threading.RLock()
_passports: Dict[str, Dict] = {}
_email_index: Dict[str, str] = {}   # corporate email -> player_id (stable identity)
_events: List[Dict] = []
_ledger: List[Dict] = []      # [{player_id, name, points, at}] — point-earning record
_day_start: float = 0.0       # manual "new day" marker (0 = use clock day)
_event_start: float = 0.0     # manual "new event" marker (0 = all-time)
_settings: Dict[str, str] = {}   # editable runtime settings (e.g. event_name)


def get_setting(key: str, default: str = "") -> str:
    return _settings.get(key, default)


def set_setting(key: str, value: str) -> None:
    with _lock:
        _settings[key] = value
        _save()


def _layers_covered(stamps: Dict) -> set:
    return {LAYER_BY_ID.get(cid) for cid in stamps}


def _now() -> float:
    # Note: time.time() is fine here (runtime state, not a cached prompt).
    return time.time()


def create_passport(name: str, email: str = "", human_verified: bool = True) -> Dict:
    """Create a passport, or resume an existing one when a corporate email is
    supplied and already known (same player across devices / a return visit)."""
    with _lock:
        em = (email or "").strip().lower()[:120]
        if em and em in _email_index:
            existing = _passports.get(_email_index[em])
            if existing is not None:
                if name.strip():
                    existing["name"] = name.strip()[:40]
                    _save()
                return existing
        clean = name.strip()[:40]
        # Anonymous players are not allowed — a real name is required.
        if not clean or clean.lower() == "anonymous":
            raise NameRequiredError("Please enter your name to start.")
        # Without an email, enforce unique screen names (email disambiguates).
        if not em:
            for q in _passports.values():
                if q["name"].lower() == clean.lower():
                    raise NameTakenError(
                        f"Screen name '{clean}' is taken — pick another or add "
                        "your corporate email."
                    )
        pid = uuid.uuid4().hex[:8]
        p = {
            "id": pid,
            "name": clean,
            "email": em,           # stored to identify players; never shown publicly
            "human_verified": bool(human_verified),
            "points": 0,
            "stamps": {},          # challenge_id -> {points, at}
            "completed": False,
            # per-session scratch state (chat history, boss-level progress…)
            "sessions": {},
            "created_at": _now(),
        }
        _passports[pid] = p
        if em:
            _email_index[em] = pid
        _save()
        return p


def get_passport(pid: str) -> Optional[Dict]:
    return _passports.get(pid)


def get_by_email(email: str) -> Optional[Dict]:
    pid = _email_index.get((email or "").strip().lower()[:120])
    return _passports.get(pid) if pid else None


def session(pid: str, key: str) -> Dict:
    """Per-passport scratch dict for a station."""
    p = get_passport(pid)
    if p is None:
        return {}
    return p["sessions"].setdefault(key, {})


def _record_points(pid: str, name: str, points: int) -> None:
    if points:
        _ledger.append({"player_id": pid, "name": name, "points": points, "at": _now()})


def award(pid: str, challenge_id: str, extra: int = 0) -> Optional[Dict]:
    """Stamp a challenge once and award points. Re-clearing only adds `extra`
    (e.g. jailbreak-wall bonuses) without double-counting the base stamp."""
    with _lock:
        p = get_passport(pid)
        if p is None:
            return None
        first_time = challenge_id not in p["stamps"]
        base = CLEAR_POINTS.get(challenge_id, 0) if first_time else 0
        gained = base + extra
        if first_time:
            p["stamps"][challenge_id] = {"points": gained, "at": _now()}
        else:
            p["stamps"][challenge_id]["points"] += gained
        p["points"] += gained
        total = gained
        # Full passport = one challenge cleared in each layer (V/C/G). Once.
        if not p["completed"] and set(LAYERS) <= _layers_covered(p["stamps"]):
            p["completed"] = True
            p["points"] += FULL_PASSPORT_BONUS
            total += FULL_PASSPORT_BONUS
        _record_points(pid, p["name"], total)
        _save()
        return p


def add_event(challenge_id: str, kind: str, summary: str, **detail) -> Dict:
    """Append to the AI Guard / activity log (the 'blocked-activity timeline')."""
    with _lock:
        ev = {
            "id": len(_events) + 1,
            "challenge": challenge_id,
            "kind": kind,             # blocked | redacted | denied | allowed | info
            "summary": summary,
            "detail": detail,
            "at": _now(),
        }
        _events.append(ev)
        return ev


def events(challenge_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
    with _lock:
        items = _events if challenge_id is None else [
            e for e in _events if e["challenge"] == challenge_id
        ]
        return list(reversed(items[-limit:]))


def _cutoff(window: str) -> float:
    """Epoch start of the requested window."""
    now = _now()
    if window == "event":
        return _event_start
    lt = time.localtime(now)
    if window == "hour":
        return now - (lt.tm_min * 60 + lt.tm_sec)
    if window == "day":
        clock_day = now - (lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec)
        return max(_day_start, clock_day)
    return _event_start


def leaderboard(window: str = "event", limit: int = 20) -> List[Dict]:
    """Ranked board over a time window: 'hour' | 'day' | 'event'."""
    window = window if window in WINDOWS else "event"
    with _lock:
        cutoff = _cutoff(window)
        agg: Dict[str, Dict] = {}
        for e in _ledger:
            if e["at"] < cutoff:
                continue
            row = agg.setdefault(
                e["player_id"], {"name": e["name"], "points": 0, "first_at": e["at"]}
            )
            row["name"] = e["name"]
            row["points"] += e["points"]
            row["first_at"] = min(row["first_at"], e["at"])
        ranked = sorted(agg.items(), key=lambda kv: (-kv[1]["points"], kv[1]["first_at"]))
        out = []
        for i, (pid, row) in enumerate(ranked[:limit]):
            p = _passports.get(pid)
            out.append({
                "rank": i + 1,
                "name": row["name"],
                "points": row["points"],
                "stamps": len(p["stamps"]) if p else 0,
                "completed": bool(p and p["completed"]),
            })
        return out


def reset_tenant() -> None:
    """Full reset — clears passports, events, AND the points ledger (new event /
    nuclear option)."""
    with _lock:
        _passports.clear()
        _email_index.clear()
        _events.clear()
        _ledger.clear()
        global _day_start, _event_start
        _day_start = 0.0
        _event_start = 0.0
        _save()


def new_day() -> None:
    """Start a new daily leaderboard window (keeps the all-conference ledger)."""
    global _day_start
    with _lock:
        _day_start = _now()
        _save()


def new_event() -> None:
    """Start a fresh all-conference board (clears the ledger; keeps active play)."""
    global _event_start, _day_start
    with _lock:
        _ledger.clear()
        _event_start = _now()
        _day_start = _now()
        _save()


def reset_passport_session(pid: str, key: str) -> None:
    """Per-station reset between attendees (clear chat, boss progress, etc.)."""
    p = get_passport(pid)
    if p is not None:
        p["sessions"].pop(key, None)


# --------------------------------------------------------------------------- #
# SQLite persistence (opt-in via BOOTH_PERSIST=1)
# --------------------------------------------------------------------------- #
def _db():
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, val TEXT)")
    return conn


def _save() -> None:
    """Write the durable state (passports w/o ephemeral sessions, ledger, email
    index, markers, settings). Called under _lock after every mutation."""
    if not _PERSIST:
        return
    try:
        slim = {
            pid: {k: v for k, v in p.items() if k != "sessions"}
            for pid, p in _passports.items()
        }
        blob = {
            "passports": slim,
            "ledger": _ledger,
            "email_index": _email_index,
            "markers": {"day_start": _day_start, "event_start": _event_start},
            "settings": _settings,
        }
        conn = _db()
        conn.execute(
            "INSERT INTO kv(key, val) VALUES('state', ?) "
            "ON CONFLICT(key) DO UPDATE SET val=excluded.val",
            (json.dumps(blob),),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # persistence must never break the booth


def _load() -> None:
    if not _PERSIST:
        return
    global _day_start, _event_start
    try:
        conn = _db()
        row = conn.execute("SELECT val FROM kv WHERE key='state'").fetchone()
        conn.close()
        if not row:
            return
        blob = json.loads(row[0])
        for pid, p in blob.get("passports", {}).items():
            p.setdefault("sessions", {})
            _passports[pid] = p
        _ledger.extend(blob.get("ledger", []))
        _email_index.update(blob.get("email_index", blob.get("badge_index", {})))
        _settings.update(blob.get("settings", {}))
        m = blob.get("markers", {})
        _day_start = m.get("day_start", 0.0)
        _event_start = m.get("event_start", 0.0)
    except Exception:
        pass


_load()
