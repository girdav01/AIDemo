# 02 · Stop the Leak

- **Capability:** AI Guard (sensitive-data filtering / redaction)
- **Pillar:** Control · **Tier:** Everyone (finance & healthcare favorite)
- **Objective:** PII and secrets are redacted/blocked before they leave the
  model; every blocked leak is visible on a timeline (the compliance story).
- **App integration point:** `POST /api/challenges/stop-the-leak/chat`;
  timeline via `GET /api/events?challenge=stop-the-leak`.

## Provision on the Vision One side

1. A demo GenAI app with a small **knowledge base** seeded with a synthetic
   "customer file" and a fake config.
2. Put **AI Guard** on the output path with **sensitive-data filtering** enabled
   (PII + secrets), set to **redact/block**.
3. Open the **blocked-activity timeline** so redactions accumulate visibly.

## Synthetic content to plant (SYNTHETIC ONLY)

- SSN `000-00-0000`
- Test card `4111 1111 1111 1111`
- API key `sk-DEMO-NOT-REAL`
- A customer file (name, SSN, card, account) and a config file containing the key.

## Policy / config

- Detectors: **SSN, payment card (PAN), API keys/secrets**, plus account numbers
  and email.
- Action: **redact** (e.g. `[REDACTED-SSN]`) or block the response.
- Ensure each redaction creates a **timeline event** (type, count).

## Clears when

The requested sensitive values come back **redacted/blocked** and the event
**shows in the blocked-activity timeline**.

## The reveal

Point at the timeline: "visibility into every blocked leak over time — the
compliance story for OSFI, HIPAA, PCI."

## Reset

Clear the session. Remind attendees **never to type real PII** — synthetic only.

## Fallback

Booth app Stop the Leak station (deterministic redaction of the same seeded data)
+ recorded demo.

## Verify in console

- ⚠️ Which sensitive-data detectors are on by default vs need enabling.
- ⚠️ Redact-vs-block action and how it renders to the user.
- ⚠️ Timeline view scoping/filtering for the booth.
