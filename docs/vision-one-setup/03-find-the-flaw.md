# 03 · Find the Flaw

- **Capability:** AI Scanner (pre-deployment scanning)
- **Pillar:** Visibility · **Tier:** Builder
- **Objective:** Catch AI app/model vulnerabilities before deploy — shift-left,
  scan-before-you-ship. Attendee names the OWASP LLM category of the top finding.
- **App integration point:** `GET /api/challenges/find-the-flaw/scan`,
  `POST .../answer`.

## Provision on the Vision One side

1. Load a **deliberately weak demo model/app** into **AI Scanner**.
2. Run a scan and **save the finished result** so the station has zero wait.
3. Have the findings view open, sorted so the **top finding is LLM01**.

## Synthetic content to plant (seeded weaknesses)

| Rank | Finding | OWASP LLM |
|------|---------|-----------|
| 1 | Injection-susceptible system prompt | **LLM01 Prompt Injection** |
| 2 | Exposed tool with no authorization | LLM06 Excessive Agency |
| 3 | Verbose error leaks stack details | LLM05 Improper Output Handling |

## Interaction / grading

- Attendee reads the report and names the OWASP category of the **top finding**.
- Accept close answers: "prompt injection", "injection", "LLM01".
- Bonus discussion: spot the secondary findings (excessive agency / insecure
  output handling).

## Clears when

Attendee **correctly names the OWASP LLM risk** for the top finding.

## The reveal

"AI Application Security covers **9 of the OWASP Top 10 for LLMs** — and only
**37%** of orgs scan AI before rollout. Scanner closes that gap."

## Reset

Re-select the pre-saved scan result; clear attendee notes.

## Fallback

Booth app Find the Flaw station serves the same 3 findings + grades the answer.

## Verify in console

- ⚠️ How to save/recall a scan result for instant display.
- ⚠️ Whether AI Scanner labels findings with explicit OWASP LLM IDs (if not, map
  them on the staff card).
