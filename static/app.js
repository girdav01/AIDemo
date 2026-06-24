// TrendAI Vision One AI Security Challenge — booth frontend
const state = { meta: null, challenges: [], pid: null, me: null, active: null, lbWindow: "event" };

const $ = (s, r = document) => r.querySelector(s);
const el = (tag, props = {}, html = "") => {
  const e = document.createElement(tag);
  Object.assign(e, props);
  if (html) e.innerHTML = html;
  return e;
};
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

async function api(path, body) {
  const opts = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : {};
  const r = await fetch(path, opts);
  if (!r.ok) {
    const t = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(t.detail || "Request failed");
  }
  return r.json();
}

// ---------- bootstrap ----------
async function init() {
  state.meta = await api("/api/meta");
  state.challenges = (await api("/api/challenges")).challenges;
  $("#event").textContent = "AI Security Challenge · " + state.meta.event;
  $("#botmode").textContent = "Bot: " + (state.meta.live_bot ? "live " + state.meta.model : "offline (deterministic)");
  renderStations();
  renderHumanCheck();
  initMarquee();
  restorePlayer();
  document.querySelectorAll(".lbtab").forEach((b) => {
    b.onclick = () => {
      state.lbWindow = b.dataset.w;
      document.querySelectorAll(".lbtab").forEach((x) => x.classList.add("ghost"));
      b.classList.remove("ghost");
      refreshSidebar();
    };
  });
  refreshSidebar();
  setInterval(refreshSidebar, 5000);
}

function restorePlayer() {
  // Resume by link (?p=ID) — e.g. scanning a personal e-passport QR.
  const fromUrl = new URLSearchParams(location.search).get("p");
  const saved = fromUrl || localStorage.getItem("v1_pid");
  if (saved) {
    api("/api/passport/" + saved).then((p) => { setPlayer(p); }).catch(() => localStorage.removeItem("v1_pid"));
  }
}

// Rolling marketing banner in the title bar, fed by static/banners.yml.
async function initMarquee() {
  const span = $("#marqueeText");
  if (!span) return;
  let cfg = { interval_seconds: 7, messages: [] };
  try { cfg = await api("/api/banners"); } catch (e) { /* leave empty */ }
  const msgs = (cfg.messages || []).filter(Boolean);
  if (!msgs.length) { $("#marquee").style.display = "none"; return; }
  const interval = Math.max(3, cfg.interval_seconds || 7) * 1000;
  let i = 0;
  const show = () => {
    span.classList.remove("show");
    setTimeout(() => { span.textContent = "📣 " + msgs[i % msgs.length]; span.classList.add("show"); }, 450);
    i++;
  };
  show();
  if (msgs.length > 1) setInterval(show, interval);
}

// On-theme human verification — tap the human emoji. Booth gate, not security.
function renderHumanCheck(msg) {
  const box = $("#humanCheck");
  if (!box) return;
  state.humanOK = false;
  $("#startBtn").disabled = true;
  const opts = ["🧑", "🤖", "👾", "🛸"];
  for (let i = opts.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [opts[i], opts[j]] = [opts[j], opts[i]];
  }
  box.innerHTML = "";
  const q = el("span", { className: "q" }, msg || "Verify you're human — tap the person:");
  if (msg) q.style.color = "var(--bad)";
  box.appendChild(q);
  opts.forEach((e) => {
    const b = el("button", { className: "he", type: "button" }, e);
    b.onclick = () => {
      if (e === "🧑") {
        state.humanOK = true;
        $("#startBtn").disabled = false;
        box.innerHTML = '<span class="ok">✓ Human verified — welcome!</span>';
      } else {
        renderHumanCheck("Nope — that's an AI. Humans only; tap the person:");
      }
    };
    box.appendChild(b);
  });
}

$("#startBtn").onclick = async () => {
  if (!state.humanOK) { alert("Please complete the human check first."); return; }
  const name = $("#nameInput").value.trim();
  if (!name) { alert("Please enter your name to start."); $("#nameInput").focus(); return; }
  const email = $("#emailInput").value.trim();
  try {
    const p = await api("/api/passport", { name, email, human_verified: true });
    setPlayer(p);
  } catch (e) {
    alert(e.message); // e.g. screen name taken — pick another or add your corporate email
  }
};
$("#newBtn").onclick = () => { localStorage.removeItem("v1_pid"); state.pid = null; state.me = null; location.reload(); };
$("#logToggle").onclick = () => {
  const wrap = $("#logWrap");
  const hidden = wrap.classList.toggle("hidden");
  $("#logToggle").textContent = hidden ? "Show" : "Hide";
};
$("#closePanel").onclick = () => { $("#panel").classList.add("hidden"); state.active = null; };

function setPlayer(p) {
  state.pid = p.id; state.me = p;
  localStorage.setItem("v1_pid", p.id);
  $("#passportBar").classList.add("hidden");
  $("#meBar").classList.remove("hidden");
  $("#epassLink").href = "/passport?p=" + p.id;
  renderMe();
}

function layersCovered() {
  const stamps = (state.me && state.me.stamps) || {};
  const byId = Object.fromEntries(state.challenges.map((c) => [c.id, c.layer]));
  const set = new Set(Object.keys(stamps).map((id) => byId[id]));
  return ["Visibility", "Control", "Governance"].map((p) => ({ p, on: set.has(p) }));
}

function renderMe() {
  if (!state.me) return;
  $("#meName").textContent = state.me.name;
  $("#mePts").textContent = state.me.points + " pts";
  const n = Object.keys(state.me.stamps || {}).length;
  $("#meStamps").textContent = n + " / " + state.challenges.length + " stamps";
  const pills = layersCovered().map((x) => `${x.p[0]}${x.on ? "✓" : "—"}`).join(" · ");
  $("#meDone").textContent = state.me.completed ? "✅ Full passport (all layers)!" : pills;
  renderStations();
}

async function refreshMe() {
  if (!state.pid) return;
  state.me = await api("/api/passport/" + state.pid);
  renderMe();
}

// ---------- stations ----------
function renderStations() {
  const grid = $("#stationGrid");
  grid.innerHTML = "";
  const done = state.me ? state.me.stamps || {} : {};
  state.challenges.forEach((c) => {
    const d = !!done[c.id];
    const card = el("div", { className: "station" + (d ? " done" : "") });
    card.innerHTML = `
      <span class="stamp">✔ STAMPED</span>
      <span class="num">${c.number}</span>
      <div class="tier">${esc(c.tier)} · ${esc(c.layer)} · ${esc(c.capability)}</div>
      <h3>${esc(c.name)}</h3>
      <div class="cap">${esc(c.owasp)}</div>
      <div class="muted" style="font-size:12px;margin-top:6px">${esc(c.mission)}</div>`;
    card.onclick = () => openPanel(c);
    grid.appendChild(card);
  });
}

function needPlayer() {
  if (!state.pid) { alert("Start a passport first."); return true; }
  return false;
}

function openPanel(c) {
  if (needPlayer()) return;
  state.active = c;
  $("#panel").classList.remove("hidden");
  $("#panelTitle").textContent = `${c.number}. ${c.name}`;
  $("#panelMeta").innerHTML = `<span class="pill">${esc(c.tier)}</span>
    <span class="pill">${esc(c.capability)}</span>
    <span class="pill">${esc(c.owasp)}</span> &nbsp; ${esc(c.clears_when)}`;
  $("#panel").scrollIntoView({ behavior: "smooth", block: "nearest" });
  ({
    "break-the-bot": renderBreakTheBot,
    "stop-the-leak": renderStopTheLeak,
    "find-the-flaw": renderFindTheFlaw,
    "trace-the-poison": renderTracePoison,
    "shadow-ai": renderShadowAI,
    "tame-the-agent": renderTameTheAgent,
    "watch-mcp-wire": renderWatchMcpWire,
    "boss-level": renderBossLevel,
  })[c.id]();
}

function starters(list, onPick) {
  if (!list.length) return "";
  const wrap = el("div", { className: "row", style: "margin:8px 0" });
  list.forEach((s) => {
    const b = el("span", { className: "starter" }, esc(s));
    b.onclick = () => onPick(s);
    wrap.appendChild(b);
  });
  return wrap;
}

function banner(kind, html) { return `<div class="banner ${kind}">${html}</div>`; }

// ---------- 1. Break the Bot ----------
function renderBreakTheBot() {
  const body = $("#panelBody");
  body.innerHTML = `
    <p class="muted">Make the bot leak the planted secret or ignore its rules.
      You clear the station when AI Guard <b>blocks &amp; logs</b> your attempt.</p>
    <div class="toggle"><label><input type="checkbox" id="grd" checked /> AI Guard ON</label>
      <span class="muted" style="font-size:12px">Staff: toggle OFF for the 30-second before/after reveal.</span></div>
    <div class="chatlog" id="chat"></div>
    <div id="startersBox"></div>
    <div class="row" style="margin-top:8px">
      <textarea id="msg" placeholder="Type a jailbreak attempt…"></textarea>
    </div>
    <div class="row"><button id="send">Send</button>
      <button class="ghost" id="vote">Crowd-favorite vote (+10)</button></div>
    <div id="bbResult"></div>`;
  const sb = $("#startersBox");
  sb.appendChild(starters(state.active.starters, (s) => { $("#msg").value = s; }));
  $("#send").onclick = sendBB;
  $("#vote").onclick = async () => { await api("/api/challenges/break-the-bot/vote", { player_id: state.pid }); await refreshMe(); refreshSidebar(); };
}
function pushChat(role, text) {
  const c = $("#chat");
  c.appendChild(el("div", { className: "msg " + role }, `<b>${role === "user" ? "You" : "HelpBot"}:</b> ${esc(text)}`));
  c.scrollTop = c.scrollHeight;
}
async function sendBB() {
  const msg = $("#msg").value.trim(); if (!msg) return;
  const guard = $("#grd").checked;
  pushChat("user", msg); $("#msg").value = "";
  try {
    const r = await api("/api/challenges/break-the-bot/chat",
      { player_id: state.pid, message: msg, guardrails_on: guard });
    pushChat("bot", r.reply);
    let out = "";
    if (r.cleared && r.bypass) out = banner("gold", `🏆 <b>BYPASS!</b> +${r.score.total} pts. Flag the booth lead.`);
    else if (r.cleared) out = banner("good", `✔ Blocked &amp; logged — station cleared! +${r.score.total} pts ` +
      r.score.breakdown.map((b) => `<span class="pill">${esc(b.label)} +${b.points}</span>`).join(" "));
    else if (r.leaked) out = banner("bad", "⚠️ Guard OFF — the bot leaked the secret. This is the reveal: toggle ON and try again.");
    $("#bbResult").innerHTML = out;
    await refreshMe(); refreshSidebar();
  } catch (e) { $("#bbResult").innerHTML = banner("bad", esc(e.message)); }
}

// ---------- 2. Stop the Leak ----------
function renderStopTheLeak() {
  const body = $("#panelBody");
  body.innerHTML = `
    <p class="muted">Try to coax the app into spilling fake PII or secrets.
      You clear it when AI Guard <b>redacts</b> the sensitive fields.</p>
    <div id="startersBox2"></div>
    <textarea id="msg2" placeholder="Ask the app to dump the customer file or config…"></textarea>
    <div class="row"><button id="send2">Send</button></div>
    <div id="slResult"></div>`;
  $("#startersBox2").appendChild(starters(state.active.starters, (s) => { $("#msg2").value = s; }));
  $("#send2").onclick = async () => {
    const msg = $("#msg2").value.trim(); if (!msg) return;
    const r = await api("/api/challenges/stop-the-leak/chat", { player_id: state.pid, message: msg });
    let html = `<h3>App response (after AI Guard)</h3><pre>${esc(r.redacted)}</pre>`;
    if (r.cleared) {
      html += banner("good", `✔ AI Guard redacted ${r.findings.length} field(s) — station cleared! ` +
        [...new Set(r.findings.map((f) => f.type))].map((t) => `<span class="pill">${t}</span>`).join(" "));
    } else html += banner("bad", esc(r.message));
    $("#slResult").innerHTML = html;
    await refreshMe(); refreshSidebar();
  };
}

// ---------- 3. Find the Flaw ----------
async function renderFindTheFlaw() {
  const body = $("#panelBody");
  body.innerHTML = `<p class="muted">Loading scan…</p>`;
  const rep = await api("/api/challenges/find-the-flaw/scan");
  const rows = rep.findings.map((f) => `<tr>
    <td>${f.rank}</td><td class="sev-${f.severity}">${f.severity}</td>
    <td>${esc(f.title)}<br><span class="muted" style="font-size:12px">${esc(f.detail)}</span></td></tr>`).join("");
  const top = rep.findings.find((f) => f.rank === 1);
  body.innerHTML = `
    <p class="muted">AI Scanner finished a pre-deployment scan of a deliberately weak app.
      Name the OWASP LLM category behind the <b>top finding</b>.</p>
    <table><thead><tr><th>#</th><th>Severity</th><th>Finding</th></tr></thead><tbody>${rows}</tbody></table>
    <p class="muted" style="font-size:12px;margin-top:10px">${esc(rep.coverage_note)}</p>
    <div class="row" style="margin-top:8px">
      <input id="owaspAns" placeholder="e.g. prompt injection / LLM01" style="flex:1" />
      <button id="ansBtn">Submit for top finding</button></div>
    <div id="ffResult"></div>`;
  $("#ansBtn").onclick = async () => {
    const ans = $("#owaspAns").value.trim(); if (!ans) return;
    const r = await api("/api/challenges/find-the-flaw/answer",
      { player_id: state.pid, finding_id: top.id, answer: ans });
    $("#ffResult").innerHTML = banner(r.correct ? "good" : "bad", esc(r.message) + (r.cleared ? " Station cleared!" : ""));
    await refreshMe(); refreshSidebar();
  };
}

// ---------- 4. Trace the Poison ----------
async function renderTracePoison() {
  const body = $("#panelBody");
  body.innerHTML = `<p class="muted">Loading Code Security scan…</p>`;
  const r = await api("/api/challenges/trace-the-poison/scan");
  const findings = r.findings.map((f) => `<tr>
    <td class="sev-${f.severity}">${f.severity}</td>
    <td>${esc(f.type)}<br><span class="muted" style="font-size:12px">${esc(f.detail)}</span></td></tr>`).join("");
  const sbom = r.sbom.map((s) => `<tr>
    <td>${esc(s.component)}</td><td>${esc(s.downstream)}</td>
    <td>${s.flagged ? '<span class="sev-High">⚠ ' + esc(s.why) + "</span>" : '<span class="muted">ok</span>'}</td></tr>`).join("");
  body.innerHTML = `
    <p class="muted">Code Security scanned <b>${esc(r.repo)}</b>. Find the leaked secret and the
      bad dependency, then use the SBOM to name a downstream app that ships a flagged component.</p>
    <h3>Findings</h3>
    <table><thead><tr><th>Severity</th><th>Finding</th></tr></thead><tbody>${findings}</tbody></table>
    <h3 style="margin-top:12px">SBOM — blast radius</h3>
    <table><thead><tr><th>Component</th><th>Downstream app</th><th>Status</th></tr></thead><tbody>${sbom}</tbody></table>
    <div class="row" style="margin-top:10px">
      <input id="tpSecret" placeholder="The leaked secret (e.g. AWS key)" style="flex:1" /></div>
    <div class="row">
      <input id="tpDep" placeholder="The bad dependency (typosquat or Log4Shell)" style="flex:1" /></div>
    <div class="row">
      <select id="tpApp"><option value="">Pick affected downstream app…</option>
        ${r.apps.map((a) => `<option value="${esc(a)}">${esc(a)}</option>`).join("")}</select>
      <button id="tpBtn">Submit trace</button></div>
    <div id="tpRes"></div>`;
  $("#tpBtn").onclick = async () => {
    const res = await api("/api/challenges/trace-the-poison/answer", {
      player_id: state.pid, secret: $("#tpSecret").value,
      dependency: $("#tpDep").value, downstream_app: $("#tpApp").value,
    });
    const ticks = `<span class="pill">secret ${res.secret_ok ? "✓" : "✗"}</span>
      <span class="pill">dependency ${res.dependency_ok ? "✓" : "✗"}</span>
      <span class="pill">SBOM app ${res.app_ok ? "✓" : "✗"}</span>`;
    $("#tpRes").innerHTML = ticks + banner(res.correct ? "good" : "bad",
      esc(res.message) + (res.cleared ? " Station cleared!" : ""));
    await refreshMe(); refreshSidebar();
  };
}

// ---------- 5. Shadow AI Hunt ----------
async function renderShadowAI() {
  const body = $("#panelBody");
  const d = await api("/api/challenges/shadow-ai/discovery");
  const rows = d.tools.map((t) => `<tr>
    <td>${esc(t.name)}</td><td>${esc(t.category)}</td>
    <td>${t.sanctioned ? '<span class="pill">sanctioned</span>' : '<span class="sev-High">unsanctioned</span>'}</td>
    <td>${t.users}</td><td>${esc(t.risk)}</td>
    <td class="muted" style="font-size:12px">${t.confidential_paste ? "⚠ confidential paste" : esc(t.note)}</td></tr>`).join("");
  body.innerHTML = `
    <p class="muted">AI Secure Access discovered GenAI traffic in the demo tenant.
      Count the <b>unsanctioned</b> tools, then govern the riskiest one.</p>
    <table><thead><tr><th>Tool</th><th>Category</th><th>Status</th><th>Users</th><th>Risk</th><th>Note</th></tr></thead>
      <tbody>${rows}</tbody></table>
    <div class="row" style="margin-top:10px">
      <input id="cnt" type="number" min="0" placeholder="# unsanctioned" style="width:140px" />
      <button id="cntBtn">Check count</button></div>
    <div id="cntRes"></div>
    <div class="row" style="margin-top:12px">
      <select id="toolSel">${d.tools.filter((t) => !t.sanctioned).map((t) => `<option value="${t.id}">${esc(t.name)} (${t.risk})</option>`).join("")}</select>
      <select id="actSel"><option value="block">Block</option><option value="coach">Coach</option></select>
      <button id="polBtn">Apply policy &amp; replay</button></div>
    <div id="polRes"></div>`;
  $("#cntBtn").onclick = async () => {
    const r = await api("/api/challenges/shadow-ai/count", { player_id: state.pid, count: Number($("#cnt").value || 0) });
    $("#cntRes").innerHTML = banner(r.correct ? "good" : "bad", esc(r.message));
  };
  $("#polBtn").onclick = async () => {
    const r = await api("/api/challenges/shadow-ai/policy",
      { player_id: state.pid, tool_id: $("#toolSel").value, action: $("#actSel").value });
    $("#polRes").innerHTML = banner(r.cleared ? "good" : "bad", esc(r.message) + (r.cleared ? " Station cleared!" : ""));
    await refreshMe(); refreshSidebar();
  };
}

// ---------- 6. Tame the Agent ----------
async function renderTameTheAgent() {
  const body = $("#panelBody");
  const b = await api("/api/challenges/tame-the-agent/briefing");
  body.innerHTML = `
    <p class="muted">An autonomous agent (tools: ${b.tools.join(", ")}) reads a document that contains
      a planted <b>indirect prompt injection</b>. Run it and confirm governance denies the rogue action.</p>
    <h3>Source document (poisoned)</h3><pre>${esc(b.source_doc)}</pre>
    <div class="toggle"><label><input type="checkbox" id="polOn" checked /> Governance policy ENABLED</label>
      <span class="muted" style="font-size:12px">Staff: toggle OFF to show what happens without governance.</span></div>
    <div class="row"><button id="runAgent">Run agent task</button></div>
    <div id="agentRes"></div>`;
  $("#runAgent").onclick = async () => {
    const r = await api("/api/challenges/tame-the-agent/run",
      { player_id: state.pid, policy_enabled: $("#polOn").checked });
    const trail = r.trail.map((s) => `<div class="toolcall ${s.decision}">
      <b>Step ${s.step}:</b> <code>${esc(s.tool)}</code> → ${esc(s.arg)}
      <br><span class="${s.decision === "denied" ? "k-denied" : "k-allowed"}">${s.decision.toUpperCase()}</span>
      — <span class="muted">${esc(s.reason)}</span></div>`).join("");
    $("#agentRes").innerHTML = trail +
      banner(r.cleared ? "good" : "bad", esc(r.verdict) + (r.cleared ? " Station cleared!" : ""));
    await refreshMe(); refreshSidebar();
  };
}

// ---------- 7. Watch the MCP Wire ----------
async function renderWatchMcpWire() {
  const body = $("#panelBody");
  const r = await api("/api/challenges/watch-mcp-wire/calls");
  const rows = r.calls.map((c) => `<div class="toolcall" id="mc-${c.id}">
    <div class="row" style="justify-content:space-between">
      <div><code>${esc(c.server)}</code> · <b>${esc(c.tool)}</b> → ${esc(c.arg)}</div>
      <button class="ghost" data-call="${c.id}">Block</button></div></div>`).join("");
  body.innerHTML = `
    <p class="muted">${esc(r.note)}</p>
    <p class="muted">Every agent-to-tool call flows through the gateway. Spot the call reaching
      outside its approved scope or hitting an unapproved server, then block it.</p>
    <div id="mcpCalls">${rows}</div>
    <div id="mcpRes"></div>`;
  body.querySelectorAll("button[data-call]").forEach((btn) => {
    btn.onclick = async () => {
      const res = await api("/api/challenges/watch-mcp-wire/block",
        { player_id: state.pid, call_id: btn.dataset.call });
      const box = $("#mc-" + btn.dataset.call);
      if (res.cleared) box.classList.add("denied");
      $("#mcpRes").innerHTML = banner(res.cleared ? "good" : "bad",
        esc(res.message) + (res.cleared ? " Station cleared!" : ""));
      await refreshMe(); refreshSidebar();
    };
  });
}

// ---------- 8. Boss Level ----------
let bossTimer = null;
async function renderBossLevel() {
  const body = $("#panelBody");
  body.innerHTML = `
    <p class="muted">Speed-run the Security Loop on one app before the timer ends:
      <b>scan → protect → validate → improve</b>. Then Companion summarizes the Break-the-Bot incident.</p>
    <div class="timer" id="bossTimer">3:00</div>
    <div class="loop-steps" id="loopSteps"></div>
    <div class="row" style="margin-top:8px"><button class="ghost" id="bossReset">Reset run</button></div>
    <div id="bossRes"></div>`;
  const steps = ["scan", "protect", "validate", "improve"];
  const wrap = $("#loopSteps");
  steps.forEach((s) => {
    const b = el("div", { className: "loop-step", id: "ls-" + s }, s.toUpperCase());
    b.onclick = () => bossStep(s);
    wrap.appendChild(b);
  });
  $("#bossReset").onclick = async () => {
    await api("/api/challenges/boss-level/reset", { player_id: state.pid });
    steps.forEach((s) => $("#ls-" + s).classList.remove("done"));
    $("#bossRes").innerHTML = ""; $("#bossTimer").textContent = "3:00";
    if (bossTimer) clearInterval(bossTimer);
  };
}
async function bossStep(step) {
  const r = await api("/api/challenges/boss-level/step", { player_id: state.pid, step });
  r.done.forEach((s) => $("#ls-" + s) && $("#ls-" + s).classList.add("done"));
  startBossTimer(r.remaining_seconds);
  if (r.cleared) {
    if (bossTimer) clearInterval(bossTimer);
    $("#bossRes").innerHTML = banner("gold", "🪙 " + esc(r.coin)) +
      `<h3>Vision One Companion</h3><pre>${esc(r.companion_summary)}</pre>`;
    await refreshMe(); refreshSidebar();
  } else if (r.message) {
    $("#bossRes").innerHTML = banner("bad", esc(r.message));
  }
}
function startBossTimer(remaining) {
  if (bossTimer) clearInterval(bossTimer);
  let rem = remaining;
  const paint = () => {
    const m = Math.floor(rem / 60), s = Math.floor(rem % 60);
    const t = $("#bossTimer"); if (t) t.textContent = `${m}:${String(s).padStart(2, "0")}`;
  };
  paint();
  bossTimer = setInterval(() => { rem -= 1; if (rem <= 0) { rem = 0; clearInterval(bossTimer); } paint(); }, 1000);
}

// ---------- sidebar ----------
async function refreshSidebar() {
  try {
    const lb = (await api("/api/leaderboard?window=" + state.lbWindow)).leaderboard;
    $("#leaderboard").innerHTML = lb.length
      ? lb.map((p) => `<div class="r"><span class="nm">#${p.rank} ${esc(p.name)}
          ${p.completed ? '<span class="full">✓</span>' : ""}</span>
          <span class="pts">${p.points}</span></div>`).join("")
      : '<div class="muted">No players yet.</div>';
    const log = (await api("/api/events")).events;
    $("#log").innerHTML = log.length
      ? log.slice(0, 15).map((e) => `<div class="log-item k-${e.kind}">
          <b>${e.kind.toUpperCase()}</b> · ${esc(e.summary)}</div>`).join("")
      : '<div class="muted">No activity yet.</div>';
  } catch (e) { /* ignore transient */ }
}

init();
