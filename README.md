# TrendAI Vision One AI Security Challenge — Booth App

A runnable booth experience for the **TrendAI Vision One™ AI Security Challenge**
(Ai4 2026, The Venetian, Las Vegas). Attendees pick up a **Challenge Passport**,
clear eight ~5-minute stations along the **Visibility → Control → Governance**
spine, earn stamps, and climb a live leaderboard. Each station maps to a real
shipping Vision One capability and an OWASP LLM / supply-chain category.

> **Synthetic data only.** Planted secrets, test card/SSN numbers, and RFC
> example domains. No real customer, employee, or personal data — ever.

The app runs **fully offline** with a deterministic demo bot, so it never
depends on venue Wi-Fi. Add an Anthropic API key to swap in a live Claude bot
behind Station 1.

---

## Quick start

```bash
cp .env.example .env          # optional — defaults work offline
./run.sh                      # installs deps + starts the server
```

- Booth app (attendee + staff): <http://localhost:8000/>
- Big-screen leaderboard:        <http://localhost:8000/screen>
- Electronic passport (mobile):  <http://localhost:8000/passport>

Run the tests:

```bash
pip install -r requirements.txt
pytest -q
```

### Optional: live Claude bot for "Break the Bot"

Set `ANTHROPIC_API_KEY` in `.env`. The model defaults to `claude-opus-4-8`
(override with `ANTHROPIC_MODEL`; a high-volume booth may prefer
`claude-haiku-4-5` for speed). Without a key, a deterministic offline bot is
used — recommended for booth reliability.

---

## The eight challenges

| # | Station | Layer | Tier | Capability | Clears when… |
|---|---------|--------|------|------------|--------------|
| 1 | **Break the Bot** | Control | Everyone | AI Guard | AI Guard blocks & logs your attempt |
| 2 | **Stop the Leak** | Control | Everyone | AI Guard | AI Guard redacts the sensitive data |
| 3 | **Find the Flaw** | Visibility | Builder | AI Scanner | You name the OWASP risk of the top finding |
| 4 | **Trace the Poison** | Visibility | Builder | Code Security | You name the secret, the bad dependency & a downstream app (SBOM) |
| 5 | **Shadow AI Hunt** | Control | Everyone | AI Secure Access | Your policy blocks the next risky prompt |
| 6 | **Tame the Agent** | Governance | Expert | Agentic Governance | Governance denies the rogue action |
| 7 | **Watch the MCP Wire** | Governance | Expert | Agentic Governance Gateway | The rogue MCP call is blocked at the gateway |
| 8 | **Boss Level** | Capstone | Expert | Platform + Companion | All four loop steps before the timer |

**Persona routing:** Execs / CIO / CAIO / CISO → 2 & 5. AI Builders → 3, 4, 6, 7, 8. Walk-ups → 1.
Make sure everyone hits one **Visibility**, one **Control**, and one **Governance** station.

> **Watch the MCP Wire** is a NEW July preview (conditional). It runs here as a
> deterministic gateway demo, which also serves as the recorded-demo fallback the
> runbook calls for if the live AGG MVP isn't show-stable.

### Station 1 — the reveal & the Jailbreak Wall

Station 1 has an **AI Guard ON/OFF toggle**. The 30-second before/after — block
the injection with the guard on, then toggle off and watch the same prompt leak
the planted secret `FALCON-9-ZULU` — is the highest-conversion moment. Every
staffer should run it.

Scoring (Creative Jailbreak Wall, from the runbook), applied automatically:

- **+10** any attempt AI Guard blocks and logs
- **+10 each** novel technique class (role-play, obfuscation, encoding,
  indirect, override), max **+30**
- **+15** multi-turn / chained attempt
- **+10** crowd-favorite (staff "vote" button)
- **+50** a genuine guardrail **bypass** — the secret leaks with the guard ON.
  The app flags it; **capture the prompt and tell the booth lead** (it feeds the
  product team).

The keyword detector is intentionally good-but-not-perfect, so clever attendees
can earn a real bypass.

### Scoring & leaderboard

- One cleared station → instant swag (a stamp + points).
- **Full passport = one challenge cleared in each layer** (Visibility, Control,
  Governance) → **+100 bonus**, premium swag, grand-prize draw. Extra stations and
  Boss Level score bonus points.
- **Windowed boards:** the leaderboard can show **This hour**, **Today**, or the
  running **Event** (all-conference) board — tabs on both the in-app sidebar and
  `/screen` (`?board=hour|day|event`). Points are recorded in a timestamped ledger
  and aggregated per window; clock windows use the server's local time, so set the
  booth machine to America/Los_Angeles.
- `POST /api/leaderboard/new-day` starts a fresh **daily** window (keeps the event
  board); `POST /api/leaderboard/new-event` starts a fresh **all-conference** board.
- Daily leaderboard top 3 → headline prize.
- Boss-Level finishers → "AI Fearlessly" challenge coin + a Companion-generated
  incident summary of their Break-the-Bot attack.

### Player identity, staff awards, persistence

- **AI4 badge ID (optional).** At registration an attendee can add their badge ID
  (type it, or a USB/camera scanner types it into the field). The badge is a
  **stable identity**: scanning it again — on another device or a return visit —
  resumes the same passport instead of creating a duplicate. Badge IDs are stored
  to identify players and are **never shown on the public leaderboard**.
- **Unique screen names.** Without a badge, screen names must be unique (a badge
  disambiguates, so the same name is allowed alongside one). `"Anonymous"` is exempt.
- **Staff-awarded clears.** `/staff` is a station-tablet view: scan the attendee's
  e-passport QR (or enter their player/badge id), pick the station, and mark it
  cleared — handy when the staffer drives the win instead of the attendee's phone.
- **Persistence.** Set `BOOTH_PERSIST=1` (default in `run.sh`) to write passports +
  the points ledger to SQLite (`BOOTH_DB`, default `booth_state.db`), so a restart
  doesn't wipe the board. Off by default in dev/tests (pure in-memory).

---

## Electronic passport (no paper)

The passport is **digital** — it lives on the attendee's phone, saving paper and
counter space.

- **Scan to start.** A booth poster (`dist/booth-passport-poster.pdf`) shows a QR
  to the app. The attendee scans it, enters a screen name, and their passport is
  created.
- **The wallet.** `/passport` is a mobile view showing their stamp grid, points,
  leaderboard rank, and a **personal QR** (encodes `/?p=<id>`). Scanning it
  resumes the passport on any device — phone, a station tablet, or the big screen.
- **Resume by link.** Any page accepts `?p=<id>` to restore a passport; the app
  also remembers the player in `localStorage`.

Print assets are generated from the booth runbook, not hand-maintained:

```bash
python tools/generate_pdfs.py --url https://your-booth-url/
# → dist/station-cards.pdf          (staff reference, one card per station)
# → dist/booth-passport-poster.pdf  ("Scan to start your e-passport" + QR)
```

Station cards stay **physical** (handy at each station); the passport does not.

## Booth ops

- **Reset demo tenant** (Staff panel) clears all players + the activity log — use
  at each happy-hour break. Confirm AI Guard is ON at shift start and after every
  Break-the-Bot reveal (the toggle defaults back to ON per attendee).
- **Activity log** in the sidebar is the blocked-/redacted-/denied-event timeline
  — the compliance story for HIPAA / PCI / OSFI.
- **Big-screen view** (`/screen`) auto-refreshes the leaderboard + How to Play,
  and can play the **Malicious Skill attractor video** during quiet spells:
  press **V** (or the button) to toggle, `?video=1` to start on the video,
  `?video=auto` to auto-cycle video ↔ leaderboard. Drop the file at
  `video/malicious-skill.mp4` (see `video/README.md`). Staff hook: *"That's a
  malicious agent skill getting caught — want to try it?"* → Tame the Agent (#6)
  or Watch the MCP Wire (#7).
- All stations are pre-loaded (scan results, agent runs, discovery view) for zero
  wait time.

## Rolling marketing banner

The title bar shows a rotating marketing message, fed by **`static/banners.yml`**
(served live via `GET /api/banners` — edit the file and it updates without a
restart). Set the rotation speed and messages:

```yaml
interval_seconds: 7
messages:
  - "Did you know that TrendAI offers AI Red Teaming Services? ..."
  - "If you want to control and govern your Agentic AI, ask for our ..."
```

## Vision One build instructions

`docs/vision-one-setup/` documents **what to provision on the Vision One side**
for each challenge to run live (capability, synthetic content, policy config,
clears-when mapping, reset, and fallback). Start with `00-overview.md`. The booth
app is a self-contained simulation; these docs describe the real demos it mirrors.

---

## Architecture

```
app/
  config.py         env config (offline-first; live bot optional)
  seed.py           synthetic demo-tenant data (matches the runbook exactly)
  guard.py          AI Guard: prompt-injection detection + PII redaction
  llm.py            demo bot (live Claude or deterministic offline)
  scanner.py        AI Scanner findings + OWASP grading (Challenge 3)
  code_security.py  Code Security scan + SBOM trace (Challenge 4)
  secure_access.py  Shadow AI discovery + policy (Challenge 5)
  agent_gov.py      agentic governance / audit trail (Challenge 6)
  mcp_gateway.py    Agentic Governance Gateway / MCP calls (Challenge 7)
  challenges.py     station metadata + layers + Jailbreak Wall scoring
  store.py          in-memory passports, events, leaderboard
  main.py           FastAPI routes + static serving
static/
  index.html app.js styles.css   attendee + staff UI
  passport.html passport.js      electronic passport (mobile wallet)
  screen.html                    big-screen leaderboard (hour/day/event) + video
  staff.html                     station-tablet staff-award view
tools/
  generate_pdfs.py               station cards + booth poster PDFs
  generate_screen_deck.py        booth big-screen deck (.pptx, 8 challenges)
docs/
  vision-one-setup/              per-challenge Vision One build instructions
video/                           booth video assets (Malicious Skill attractor)
tests/
  test_challenges.py             end-to-end tests for all eight stations
```

State is in-memory (single shared demo tenant); restart or "Reset demo tenant"
to clear. No database, no external dependencies required to run.

---

*Don't just build AI. Secure it. — AI Fearlessly.*
