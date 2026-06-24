"""In-memory state: passports, the activity/blocked-event log, and the
leaderboard. Single shared demo tenant. Reset between attendees / shifts."""

import threading
import time
import uuid
from typing import Dict, List, Optional

# challenge_id -> base points awarded for a clear (stamp value)
CLEAR_POINTS = {
    "break-the-bot": 10,      # base; jailbreak-wall bonuses add on top
    "stop-the-leak": 50,
    "find-the-flaw": 50,
    "shadow-ai": 50,
    "tame-the-agent": 50,
    "boss-level": 100,
}
FULL_PASSPORT_BONUS = 100

_lock = threading.RLock()
_passports: Dict[str, Dict] = {}
_events: List[Dict] = []


def _now() -> float:
    # Note: time.time() is fine here (runtime state, not a cached prompt).
    return time.time()


def create_passport(name: str) -> Dict:
    with _lock:
        pid = uuid.uuid4().hex[:8]
        p = {
            "id": pid,
            "name": name.strip()[:40] or "Anonymous",
            "points": 0,
            "stamps": {},          # challenge_id -> {points, at}
            "completed": False,
            # per-session scratch state (chat history, boss-level progress…)
            "sessions": {},
            "created_at": _now(),
        }
        _passports[pid] = p
        return p


def get_passport(pid: str) -> Optional[Dict]:
    return _passports.get(pid)


def session(pid: str, key: str) -> Dict:
    """Per-passport scratch dict for a station."""
    p = get_passport(pid)
    if p is None:
        return {}
    return p["sessions"].setdefault(key, {})


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
        # Full-passport bonus, once.
        if not p["completed"] and len(p["stamps"]) >= len(CLEAR_POINTS):
            p["completed"] = True
            p["points"] += FULL_PASSPORT_BONUS
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


def leaderboard(limit: int = 20) -> List[Dict]:
    with _lock:
        ranked = sorted(
            _passports.values(),
            key=lambda p: (-p["points"], p["created_at"]),
        )
        return [
            {
                "rank": i + 1,
                "name": p["name"],
                "points": p["points"],
                "stamps": len(p["stamps"]),
                "completed": p["completed"],
            }
            for i, p in enumerate(ranked[:limit])
        ]


def reset_tenant() -> None:
    """Full reset — clears all passports and events (happy-hour reset)."""
    with _lock:
        _passports.clear()
        _events.clear()


def reset_passport_session(pid: str, key: str) -> None:
    """Per-station reset between attendees (clear chat, boss progress, etc.)."""
    p = get_passport(pid)
    if p is not None:
        p["sessions"].pop(key, None)
