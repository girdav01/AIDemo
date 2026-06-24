// Electronic passport wallet — mobile view, auto-refreshes.
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
const ICONS = {
  "break-the-bot": "🤖", "stop-the-leak": "🛡️", "find-the-flaw": "🔍",
  "trace-the-poison": "🧪", "shadow-ai": "👁️", "tame-the-agent": "⚙️",
  "watch-mcp-wire": "🔌", "boss-level": "🏁",
};
let CH = [];
let BASE = "";   // public booth URL for QR (so it doesn't encode localhost)

function pid() {
  return new URLSearchParams(location.search).get("p") || localStorage.getItem("v1_pid");
}

async function load() {
  const id = pid();
  if (!id) { document.getElementById("loading").textContent = "No passport found. Start one at the booth."; return; }
  try {
    if (!CH.length) CH = (await (await fetch("/api/challenges")).json()).challenges;
    if (!BASE) { try { BASE = (await (await fetch("/api/meta")).json()).base_url || ""; } catch (e) {} }
    const p = await (await fetch("/api/passport/" + id)).json();
    const lb = (await (await fetch("/api/leaderboard")).json()).leaderboard;
    render(p, lb);
  } catch (e) {
    document.getElementById("loading").textContent = "Could not load passport (" + e.message + ").";
  }
}

function render(p, lb) {
  document.getElementById("loading").classList.add("hidden");
  document.getElementById("content").classList.remove("hidden");
  document.getElementById("pname").textContent = p.name;
  document.getElementById("ppts").textContent = p.points;
  const n = Object.keys(p.stamps || {}).length;
  document.getElementById("pstamps").textContent = n + " / " + CH.length + " stamps";
  const byId = Object.fromEntries(CH.map((c) => [c.id, c.layer]));
  const cov = new Set(Object.keys(p.stamps || {}).map((id) => byId[id]));
  const pills = ["Visibility", "Control", "Governance"].map((x) => x[0] + (cov.has(x) ? "✓" : "—")).join(" · ");
  document.getElementById("pdone").textContent = p.completed ? "✅ Full passport — draw entered!" : pills;
  document.getElementById("pcode").textContent = p.id;
  document.getElementById("playLink").href = "/?p=" + p.id;

  const rank = lb.find((r) => r.name === p.name);
  document.getElementById("prank").textContent = rank ? "Leaderboard #" + rank.rank : "";

  const grid = document.getElementById("stampGrid");
  grid.innerHTML = CH.map((c) => {
    const on = !!(p.stamps || {})[c.id];
    const pts = on ? p.stamps[c.id].points : 0;
    return `<div class="st ${on ? "on" : ""}">
      <div class="ic">${on ? (ICONS[c.id] || "✔") : "○"}</div>
      <div class="nm">${esc(c.name)}</div>
      <div class="tk">${on ? "+" + pts : ""}</div></div>`;
  }).join("");

  const base = (BASE || location.origin).replace(/\/$/, "");
  const url = base + "/?p=" + p.id;
  document.getElementById("qr").src = "/api/qr?data=" + encodeURIComponent(url);
}

load();
setInterval(load, 5000);
