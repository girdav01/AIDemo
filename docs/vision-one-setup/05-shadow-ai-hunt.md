# 05 · Shadow AI Hunt

- **Capability:** AI Secure Access (Zero Trust)
- **Pillar:** Control · **Tier:** Everyone (the exec / CISO win)
- **Objective:** Discover unsanctioned GenAI use and enforce policy without
  banning the tools people need.
- **App integration point:** `GET /api/challenges/shadow-ai/discovery`,
  `POST .../count`, `POST .../policy`.

## Provision on the Vision One side

1. Open the **AI Secure Access discovery view** in the demo tenant.
2. Pre-populate **simulated employee traffic** to several public GenAI tools
   (mix of sanctioned + unsanctioned).
3. Seed one event showing **"confidential" text pasted into a consumer chatbot**
   (the riskiest tool).

## Synthetic content to plant

- A handful of GenAI tools with usage counts and risk levels; mark which are
  **unsanctioned**. The booth app uses:
  - ShadowChat Public (consumer chatbot, **riskiest**, confidential paste)
  - PixelDream AI (image gen), CodeMuse Free (code), TranslateNow (translation)
  - TrendAI Companion (sanctioned)
- **Expected count = number of unsanctioned tools** (record the day's value on
  the staff card; it varies by tenant seed).

## Interaction / grading

1. Attendee filters the view and **counts unsanctioned tools**.
2. Applies a **block** or **coach** policy to the **riskiest** tool.
3. Replays the risky event.

## Clears when

Their policy **blocks (or coaches)** the next risky prompt — visible in the log.
(App: clearing requires governing the **riskiest** tool.)

## The reveal

"Every org here has a shadow-AI problem. This is how you see it and govern it
without banning the tools people need."

## Reset

Remove the attendee-created policy; reset the discovery filter.

## Fallback

Booth app Shadow AI Hunt station (discovery table, count check, block/coach +
replay).

## Verify in console

- ⚠️ How to seed/simulate discovery traffic in a demo tenant.
- ⚠️ Block vs coach policy options and where the replay/enforcement shows.
- ⚠️ The day's unsanctioned-tool count (put it on the staff card).
