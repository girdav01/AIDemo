# Booth staff quickstart

Operating guide for the **TrendAI Vision One AI Security Challenge** booth — how
to run registration, the stations, staff-driven awards, and the leaderboards.

## The four screens (URLs)

| Screen | Where | Who |
|---|---|---|
| `/` | Counter device (also what the poster QR opens on attendee phones) | Attendees register + can self-play |
| `/screen` | Big monitor | Audience — leaderboard + Malicious Skill attractor |
| `/passport` | Attendee's phone | Their e-passport wallet + personal QR |
| `/staff` | Station tablet(s) | Staff award clears |

## One-time setup (start of day)

1. Start the app: `./run.sh` (SQLite persistence is on by default, so the board
   survives a restart).
2. **Set the booth machine's clock to America/Los_Angeles** — the "This hour" /
   "Today" leaderboard windows key off server local time.
3. Open `/screen` on the big monitor. Use the **Today** tab for the daily prize,
   **Event** for the grand-prize board; `?board=hour` for an hourly giveaway.
   Press **V** for the Malicious Skill video (or open `/screen?video=auto` to
   auto-cycle video ↔ leaderboard).
4. Open `/staff` on each station tablet. Leave the **Attendee** box focused (it
   auto-focuses).
5. Optional: start a clean window — **New event** at the start of the conference,
   **New day** each morning (`POST /api/leaderboard/new-event` / `/new-day`).

## How an attendee gets registered

- They scan the **poster QR** → `/` opens on their phone → type a **screen name**
  + (optional) **AI4 badge ID** → **Start passport**.
- Or a staffer registers them at the counter device the same way.
- The badge ID is the key: if they return later or switch devices, entering the
  same badge **resumes their passport** instead of starting over.

## Running a station — two ways to award a clear

**Mode A — attendee self-drives (default).** They play the station on their own
phone; the win is detected automatically and points post instantly. Nothing for
staff to do.

**Mode B — staff-driven (the `/staff` tablet).** When the staffer runs the demo
and wants to mark the win:

1. On `/staff`, **scan the attendee's e-passport QR** (a USB/camera scanner types
   the URL and hits Enter → awards immediately), **or** type their **player id**
   or **badge id** into the box.
2. Pick the **station** from the dropdown (all 8 listed).
3. **Mark cleared** → green confirmation (e.g. `Alice cleared find-the-flaw —
   50 pts, 1/8 stamps`) and it appears in **Recent awards**. The box re-focuses
   for the next person.

The `/staff` box accepts any of: the QR URL (`…/?p=abc123`), a raw player id,
`badge:AI4-42`, or a bare badge id — whatever the scanner gives you works.

## During the day

- **Points → leaderboard is automatic** — both modes write to the same ledger;
  the big screen refreshes every 3s.
- **Hourly prize:** flip `/screen` to **This hour** and read the top.
- **Daily prize (4 PM):** **Today** tab; optionally **New day** the next morning.
- **Full passport** = one clear in each layer (Visibility · Control ·
  Governance) → the ✓ shows and they're in the grand-prize draw.

## Resets

- **Between attendees (per station):** the app clears per-station scratch (chat,
  boss timer) on its own; for Break the Bot, confirm the AI Guard toggle is back
  **ON**.
- **Happy-hour / full wipe:** Staff panel on `/` → **Reset demo tenant**
  (`/api/reset`) clears everyone — use sparingly; it also clears the board. To get
  a fresh daily number without wiping, use **New day** instead.

## Quick troubleshooting

| Symptom | Fix |
|---|---|
| "Screen name is taken" (409) | Two people picked the same name with no badge — add their badge ID, or pick a different name. |
| Scanner not awarding | Make sure the `/staff` Attendee box is focused; most scanners send Enter automatically (the page awards on Enter). |
| Board empty after restart | Persistence is on via `run.sh`; if you launched uvicorn manually, set `BOOTH_PERSIST=1`. |
| Wrong hour/day rollover | The server clock isn't on Vegas time (America/Los_Angeles). |
| Station 1 won't block | Confirm the AI Guard toggle is ON (it defaults back to ON per attendee). |

## Data handling

Synthetic data only at every station. AI4 **badge IDs** are stored server-side to
identify/resume players and are **never shown on the public leaderboard**. If
anyone enters something sensitive by mistake, clear the session and reset the
station. See the booth runbook for the full safety checklist.
