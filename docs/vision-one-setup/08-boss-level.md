# 08 · Boss Level — Close the Loop

- **Capability:** Vision One platform Security Loop + Companion
- **Pillar:** Capstone · **Tier:** Expert
- **Objective:** Speed-run the full Security Loop on one app —
  **scan → protect → validate → improve** — finishing with a **Companion**-
  generated incident summary. Beat the 3-minute timer.
- **App integration point:** `POST /api/challenges/boss-level/step`,
  `POST .../reset` (the app generates the Companion summary on completion).

## Provision on the Vision One side

1. **Pre-stage one app** that can run all four loop steps quickly:
   - **scan** — AI Scanner / Code Security result ready
   - **protect** — AI Guard policy enforced at runtime
   - **validate** — re-run / confirm the protection blocks the attack
   - **improve** — apply the recommended policy change
2. Set a **3-minute timer** (the app has one built in).
3. Have **Companion** ready to **summarize the Break-the-Bot attack** from
   Station 1 (the incident to close out).

## Interaction

Attendee completes the four steps in order, then has **Companion** summarize the
incident — before the timer ends. Use the **same demo app chain** across attempts
so timing stays consistent.

## Clears when

All four loop steps are done **before the timer ends** and **Companion returns a
clean summary**. Finishers earn the **"AI Fearlessly" challenge coin**.

## The reveal

"This is a **platform, not a point tool** — one closed loop across scan, runtime,
and SOC."

## Reset

Reset the app state and the timer.

## Fallback

Booth app Boss Level station runs the timed four-step loop and produces a
Companion-style incident summary referencing the player's Break-the-Bot attempts.

## Verify in console

- ⚠️ Which module surfaces each loop step in your tenant (so staff can narrate
  scan → protect → validate → improve consistently).
- ⚠️ How to prompt Companion for the incident summary (and whether it can pull
  the Station-1 events automatically vs a guided prompt).
- ⚠️ A repeatable demo-app chain that reliably fits under 3 minutes.
