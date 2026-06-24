# Vision One setup — Overview

What to build on the **Trend Vision One** side so each booth challenge runs live.
Each challenge has its own file (`01`–`08`) with the same structure:

- **Capability** — the Vision One module it demos.
- **Pillar** — Visibility / Control / Governance.
- **Provision on the Vision One side** — the build checklist.
- **Synthetic content to plant** — exact values (match the booth app).
- **Policy / config** — what makes the "clears when" fire.
- **Clears when** — the win condition (mirrors the app).
- **Reset** — between attendees.
- **Fallback** — if the live module isn't show-stable.
- **Verify in console** — assumptions to confirm; exact UI paths may differ by
  tenant/release.

> ⚠️ **Console navigation is not pinned here.** Module names are taken from the
> booth runbook; exact menu paths/feature flags change between releases. Treat
> every "Verify in console" note as a real to-do before show day.

## Global prerequisites

1. **One shared, non-production demo tenant.** Never connect a production or
   customer tenant. Label it clearly (e.g. `ai4-booth-demo`).
2. **Entitlements** for the AI security modules used across the eight stations:
   - AI Application Security — **AI Guard** (runtime) and **AI Scanner** (pre-deploy)
   - **Code Security** (secrets + SCA/SBOM)
   - **AI Secure Access** (Zero Trust access / shadow-AI discovery)
   - **Agentic governance** + **Agentic Governance Gateway (AGG)** — *July preview, conditional*
   - **Vision One Companion**
3. **Synthetic data only.** Planted secrets, test card/SSN numbers, and RFC
   example domains (`example.com`). No real PII, ever. (Values are listed per
   challenge and centralized in the app at `app/seed.py`.)
4. **Pre-stage everything for zero wait:** saved AI Scanner result, saved Code
   Security repo scan + SBOM, pre-built agent runs, discovery view pre-populated.
5. **Backup recordings** of every demo for venue-Wi-Fi failure.
6. **Booth accounts/roles** for staff with least privilege needed to apply demo
   policies and reset state.

## Pillar / station map

| # | Station | Pillar | Vision One capability |
|---|---------|--------|------------------------|
| 1 | Break the Bot | Control | AI Guard (runtime) |
| 2 | Stop the Leak | Control | AI Guard (sensitive-data filtering) |
| 3 | Find the Flaw | Visibility | AI Scanner |
| 4 | Trace the Poison | Visibility | Code Security (secrets + SCA + SBOM) |
| 5 | Shadow AI Hunt | Control | AI Secure Access (Zero Trust) |
| 6 | Tame the Agent | Governance | Agentic governance |
| 7 | Watch the MCP Wire | Governance | Agentic Governance Gateway (AGG) |
| 8 | Boss Level | Capstone | Platform Security Loop + Companion |

Passport completion = one cleared challenge in **each** of Visibility, Control,
Governance. Boss Level is the capstone/bonus.

## How the app and the live demo relate

The booth app emulates each challenge end-to-end so the leaderboard, passport,
and activity log work with no tenant. To run live, you drive the **real** Vision
One module for the attendee-facing moment, and still record the clear in the app
(scan the e-passport / enter the player code at the station) so scoring and the
leaderboard stay consistent. Each challenge file calls out the integration point.

## Integrating live results back into the leaderboard (optional)

If you want live module actions to award points automatically (instead of a
staffer marking the clear in the app), the app exposes per-challenge endpoints
(see each file's "Integration point"). The thin path is: keep the app as the
system of record for scoring; have staff confirm the clear in the app UI after
the live module shows the win. A deeper integration (webhook from Vision One →
app award endpoint) is possible but out of scope for v1.
