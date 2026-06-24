# 07 · Watch the MCP Wire

- **Capability:** Agentic Governance Gateway (AGG) — LLM + MCP proxy
- **Layer:** Governance · **Tier:** Expert · **NEW July preview (conditional)**
- **Objective:** Show the gateway as the single governed choke point in front of
  an agent: full visibility into every MCP tool-call, policy enforced in one
  place.
- **App integration point:** `GET /api/challenges/watch-mcp-wire/calls`,
  `POST .../block`.

## Provision on the Vision One side

1. **If the AGG MVP is demo-stable by show time:** route a live agent's **MCP
   traffic through the gateway** and open the **call dashboard** (per-call
   request/response visibility).
2. Configure a **scope/allowlist policy** (approved MCP servers; approved paths
   per server).
3. Plant a **rogue MCP tool-call** that breaks scope.
4. **Fallback (if not ready):** run as a guided walkthrough off the **recorded
   demo + the Malicious Skill video**, and capture leads for follow-up.

## Synthetic content to plant

- A stream of MCP calls, one or two of which are rogue. The booth app uses:
  - `files · fs.read /workspace/q3-report.md` — ok
  - `db · db.query` — ok
  - `files · fs.read /etc/shadow` — **rogue** (path outside approved scope)
  - `unknown-mcp.example.com · http.fetch` — **rogue** (unapproved MCP server)
  - `files · fs.read /workspace/notes.md` — ok

## Interaction

Attendee watches calls stream through the gateway, **spots the suspicious call**
(out-of-scope path or unapproved server), and **applies a policy to block it**.

## Clears when

The disallowed MCP call is **blocked at the gateway** and **logged with full
request/response visibility**.

## The reveal

"Every agent-to-tool call flows through one governed choke point — **LiteLLM-
native and MCP-aware**. That's how you govern agents without rewriting them."

## Reset

Restore the default gateway policy; reset the demo agent run.

## Fallback

This station is **conditional**. The booth app provides a deterministic gateway
demo (spot + block the rogue call) that **is** the recorded-demo fallback; pair
with the Malicious Skill attractor video on the screen.

## Verify in console

- ⚠️ AGG preview availability/flagging for the demo tenant at show time.
- ⚠️ How MCP servers/scopes are registered and how a block policy is authored.
- ⚠️ Whether the call dashboard shows full request/response for the booth.
- ⚠️ Decision deadline to commit live vs fallback (put on the setup checklist).
