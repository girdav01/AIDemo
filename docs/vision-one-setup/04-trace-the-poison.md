# 04 · Trace the Poison

- **Capability:** Code Security (secret scanning + SCA + SBOM)
- **Pillar:** Visibility · **Tier:** Builder (supply-chain story)
- **Objective:** Catch a hardcoded secret and a malicious/vulnerable dependency
  before deploy, then use the **SBOM** to trace the blast radius to a downstream
  app.
- **App integration point:** `GET /api/challenges/trace-the-poison/scan`,
  `POST .../answer`.

## Provision on the Vision One side

1. Create a **seeded demo repo** and connect it to **Code Security**.
2. Run the scan (secrets + **SCA**) and **generate the SBOM**; save both so the
   station has zero wait.
3. Have the findings view and the SBOM/dependency graph open.

## Synthetic content to plant (ALL SYNTHETIC)

- **Hardcoded secret:** AWS key `AKIA-DEMO-NOTREAL` in a config file.
- **Typosquatted package:** `reqeusts` (standing in for `requests`).
- **Vulnerable transitive dep:** a pinned Log4Shell-era version
  (`log4j-core 2.14.1`, CVE-2021-44228) flagged by SCA.
- **SBOM → downstream apps** (so the trace has an answer):
  - `reqeusts` → `billing-api` (flagged)
  - `log4j-core 2.14.1` → `analytics-service` (flagged)
  - clean components → `web-frontend`

## Interaction / grading

Attendee must identify **all three**:
1. the exposed secret (the AWS key),
2. the malicious/vulnerable dependency (typosquat **or** Log4Shell),
3. **a downstream app** from the SBOM that ships a flagged component
   (`billing-api` or `analytics-service`).

## Clears when

They name the **secret + the bad dependency + one affected downstream app**.

## The reveal

"XZ Utils, Log4Shell, the npm and PyPI typosquats — this is how you answer
'are we exposed?' in minutes, with the **SBOM as your map**."

## Reset

Re-select the saved scan result and SBOM; clear attendee notes.

## Fallback

Booth app Trace the Poison station presents the findings + SBOM and grades the
three-part answer.

## Verify in console

- ⚠️ Code Security onboarding for a demo repo + where SBOM generation lives.
- ⚠️ Whether the typosquat is flagged by malicious-package detection vs SCA.
- ⚠️ How the dependency→downstream-app mapping is shown (graph vs table).
