# Vision One AI Security Challenge — Booth App

A runnable booth experience for the **TrendAI Vision One™ AI Security Challenge**
(Ai4 2026, The Venetian, Las Vegas). Attendees pick up a **Challenge Passport**,
clear six ~5-minute stations, earn stamps, and climb a live leaderboard. Each
station maps to a real shipping Vision One capability and an OWASP LLM Top-10
category.

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

## The six challenges

| # | Station | Tier | Capability | OWASP | Clears when… |
|---|---------|------|------------|-------|--------------|
| 1 | **Break the Bot** | Everyone | AI Guard | LLM01 Prompt Injection | AI Guard blocks & logs your attempt |
| 2 | **Stop the Leak** | Everyone | AI Guard | LLM02 Sensitive Info Disclosure | AI Guard redacts the sensitive data |
| 3 | **Find the Flaw** | Builder | AI Scanner | LLM01 / LLM05 / LLM06 | You name the OWASP risk of the top finding |
| 4 | **Shadow AI Hunt** | Everyone | AI Secure Access | Governance / Zero Trust | Your policy blocks the next risky prompt |
| 5 | **Tame the Agent** | Expert | Agentic Governance | LLM01 (indirect) / LLM06 | Governance denies the rogue action |
| 6 | **Boss Level** | Expert | Platform + Companion | Full Security Loop | All four loop steps before the timer |

**Persona routing:** Execs/CISOs → 2 & 4. Builders → 3, 5, 6. Walk-ups → 1.

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
- Full passport (all six) → **+100 bonus**, premium swag, grand-prize draw.
- Daily leaderboard top 3 → headline prize.
- Boss-Level finishers → "AI Fearlessly" challenge coin + a Companion-generated
  incident summary of their Break-the-Bot attack.

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
- **Big-screen view** (`/screen`) auto-refreshes the leaderboard + How to Play.
- All stations are pre-loaded (scan results, agent runs, discovery view) for zero
  wait time.

---

## Architecture

```
app/
  config.py         env config (offline-first; live bot optional)
  seed.py           synthetic demo-tenant data (matches the runbook exactly)
  guard.py          AI Guard: prompt-injection detection + PII redaction
  llm.py            demo bot (live Claude or deterministic offline)
  scanner.py        AI Scanner findings + OWASP grading (Challenge 3)
  secure_access.py  Shadow AI discovery + policy (Challenge 4)
  agent_gov.py      agentic governance / audit trail (Challenge 5)
  challenges.py     station metadata + Jailbreak Wall scoring
  store.py          in-memory passports, events, leaderboard
  main.py           FastAPI routes + static serving
static/
  index.html app.js styles.css   attendee + staff UI
  screen.html                    big-screen leaderboard
tests/
  test_challenges.py             end-to-end tests for all six stations
```

State is in-memory (single shared demo tenant); restart or "Reset demo tenant"
to clear. No database, no external dependencies required to run.

---

*Don't just build AI. Secure it. — AI Fearlessly.*
