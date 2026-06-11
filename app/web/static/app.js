// Mundial 2026 · Centro de Analítica
// Autor: Jeshua Romero Guadarrama
"use strict";

// Registra el service worker para que la app sea instalable en el móvil (PWA).
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js").catch(() => {});
  });
}

const $ = (s) => document.querySelector(s);
const pct = (x) => (x == null ? "—" : Math.round(x * 100) + "%");
const pct1 = (x) => (x == null ? "—" : (x * 100).toFixed(1) + "%");
const api = (p) => fetch(p).then((r) => r.json());
const COL = { home: "#3b82f6", draw: "#94a3b8", away: "#ef4444", gold: "#f5c542", green: "#00e08a" };

// FIFA (3 letras) -> ISO-2 para banderas (flagcdn)
const ISO2 = {
  ARG: "ar", URU: "uy", SRB: "rs", TUR: "tr", FRA: "fr", MAR: "ma", AUT: "at",
  GRE: "gr", ESP: "es", MEX: "mx", UKR: "ua", HUN: "hu", ENG: "gb-eng", USA: "us",
  AUS: "au", SCO: "gb-sct", BRA: "br", SUI: "ch", CAN: "ca", TUN: "tn", POR: "pt",
  SEN: "sn", POL: "pl", GHA: "gh", NED: "nl", JPN: "jp", NGA: "ng", QAT: "qa",
  BEL: "be", DEN: "dk", EGY: "eg", KSA: "sa", GER: "de", NOR: "no", ALG: "dz",
  CRC: "cr", CRO: "hr", ECU: "ec", CIV: "ci", PAN: "pa", ITA: "it", KOR: "kr",
  PER: "pe", JAM: "jm", COL: "co", IRN: "ir", PAR: "py", NZL: "nz",
  WAL: "gb-wls", CMR: "cm",
  CZE: "cz", RSA: "za", BIH: "ba", HAI: "ht", CUW: "cw", SWE: "se",
  CPV: "cv", IRQ: "iq", JOR: "jo", UZB: "uz", COD: "cd",
};
let NAME2CODE = {};
const codeOf = (name) => NAME2CODE[name] || "";

// Nombres de selecciones en español (solo para mostrar; la clave interna es el inglés)
const ES = {
  "Mexico": "México", "South Korea": "Corea del Sur", "Czech Republic": "Chequia", "South Africa": "Sudáfrica",
  "Canada": "Canadá", "Bosnia and Herzegovina": "Bosnia y Herzegovina", "Qatar": "Catar", "Switzerland": "Suiza",
  "Brazil": "Brasil", "Morocco": "Marruecos", "Haiti": "Haití", "Scotland": "Escocia",
  "United States": "Estados Unidos", "Paraguay": "Paraguay", "Australia": "Australia", "Turkey": "Turquía",
  "Germany": "Alemania", "Curacao": "Curazao", "Ivory Coast": "Costa de Marfil", "Ecuador": "Ecuador",
  "Netherlands": "Países Bajos", "Japan": "Japón", "Sweden": "Suecia", "Tunisia": "Túnez",
  "Belgium": "Bélgica", "Egypt": "Egipto", "Iran": "Irán", "New Zealand": "Nueva Zelanda",
  "Spain": "España", "Cape Verde": "Cabo Verde", "Saudi Arabia": "Arabia Saudí", "Uruguay": "Uruguay",
  "France": "Francia", "Senegal": "Senegal", "Iraq": "Irak", "Norway": "Noruega",
  "Argentina": "Argentina", "Algeria": "Argelia", "Austria": "Austria", "Jordan": "Jordania",
  "Portugal": "Portugal", "DR Congo": "RD Congo", "Uzbekistan": "Uzbekistán", "Colombia": "Colombia",
  "England": "Inglaterra", "Croatia": "Croacia", "Ghana": "Ghana", "Panama": "Panamá",
};
const esName = (n) => ES[n] || n;
// Bandera + nombre en español (n = nombre interno en inglés)
const tf = (n) => `${flag(n)}${esName(n)}`;
const tfc = (code, n) => `${flag(code, true)}${esName(n)}`;
function flag(nameOrCode, isCode = false) {
  const code = isCode ? nameOrCode : codeOf(nameOrCode);
  const iso = ISO2[code];
  if (!iso) return "";
  return `<img class="flag" src="https://flagcdn.com/32x24/${iso}.png" alt="" loading="lazy" onerror="this.remove()">`;
}

const fmtDate = (iso) => {
  if (!iso) return "Fecha por confirmar";
  try { return new Date(iso).toLocaleString("es-ES", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }); }
  catch { return iso; }
};
const stageEs = (s) => ({ GROUP_STAGE: "Fase de grupos", LAST_16: "Octavos", ROUND_OF_16: "Octavos",
  QUARTER_FINALS: "Cuartos", SEMI_FINALS: "Semifinales", THIRD_PLACE: "3er puesto", FINAL: "Final" }[s] || s || "Partido");

// ---------------- motor de gráficos (SVG/CSS propio) ----------------
function donut(parts, size = 116, stroke = 15) {
  const r = (size - stroke) / 2, C = 2 * Math.PI * r, cx = size / 2;
  let off = 0;
  const arcs = parts.map((p) => {
    const len = Math.max(0, p.value) * C;
    const seg = `<circle cx="${cx}" cy="${cx}" r="${r}" fill="none" stroke="${p.color}"
      stroke-width="${stroke}" stroke-dasharray="${len} ${C - len}" stroke-dashoffset="${-off}"
      transform="rotate(-90 ${cx} ${cx})" stroke-linecap="butt"/>`;
    off += len; return seg;
  }).join("");
  const top = parts.reduce((a, b) => (b.value > a.value ? b : a), parts[0]);
  return `<svg viewBox="0 0 ${size} ${size}" width="${size}" height="${size}" class="donut">
    <circle cx="${cx}" cy="${cx}" r="${r}" fill="none" stroke="#1c2333" stroke-width="${stroke}"/>
    ${arcs}
    <text x="${cx}" y="${cx - 2}" text-anchor="middle" class="donut-big">${Math.round(top.value * 100)}%</text>
    <text x="${cx}" y="${cx + 15}" text-anchor="middle" class="donut-small">${top.label}</text>
  </svg>`;
}

function hbars(rows, { max, fmt = (v) => v, showVal = true } = {}) {
  const m = max || Math.max(...rows.map((r) => r.value), 1e-9);
  return `<div class="hbars">` + rows.map((r) => `
    <div class="bcrow">
      <span class="blabel">${r.flag || ""}${r.label}</span>
      <span class="btrack"><span class="bfill" style="width:${Math.max(2, (r.value / m) * 100)}%;background:${r.color || COL.green}"></span></span>
      ${showVal ? `<span class="bval">${fmt(r.value)}</span>` : ""}
    </div>`).join("") + `</div>`;
}

// Tarjeta contenedora de un gráfico
function chartCard(title, sub, inner, cls = "") {
  return `<div class="chart-card ${cls}"><h4>${title}</h4>${sub ? `<p class="chint">${sub}</p>` : ""}<div class="chart-body">${inner}</div></div>`;
}
// Leyenda de series
function legend(items) {
  return `<div class="rel-legend">${items.map((i) => `<span><span class="dot" style="background:${i.color}"></span>${i.label}</span>`).join("")}</div>`;
}
// Gráfico de líneas con ejes (para fiabilidad y gaps)
function lineChart(series, { diagonal = false, yRange = [0, 1], zero = false, xLabel = "" } = {}) {
  const W = 300, H = 230, pad = 34, [y0, y1] = yRange;
  const X = (v) => pad + v * (W - 2 * pad), Y = (v) => H - pad - ((v - y0) / (y1 - y0)) * (H - 2 * pad);
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" class="linec">`;
  s += `<rect x="${pad}" y="${pad}" width="${W - 2 * pad}" height="${H - 2 * pad}" fill="none" stroke="#243047"/>`;
  if (diagonal) s += `<line x1="${X(0)}" y1="${Y(0)}" x2="${X(1)}" y2="${Y(1)}" stroke="#5b6b85" stroke-dasharray="4 4"/>`;
  if (zero) s += `<line x1="${X(0)}" y1="${Y(0)}" x2="${X(1)}" y2="${Y(0)}" stroke="#5b6b85" stroke-dasharray="3 3"/>`;
  [y0, (y0 + y1) / 2, y1].forEach((t) => { s += `<text x="${pad - 6}" y="${Y(t) + 3}" fill="#8a97ad" font-size="9" text-anchor="end">${(+t).toFixed(2)}</text>`; });
  [0, 0.5, 1].forEach((t) => { s += `<text x="${X(t)}" y="${H - pad + 13}" fill="#8a97ad" font-size="9" text-anchor="middle">${t}</text>`; });
  series.forEach((se) => {
    const pts = se.points.filter((p) => p.y != null);
    if (pts.length > 1) s += `<polyline fill="none" stroke="${se.color}" stroke-width="1.7" opacity=".9" points="${pts.map((p) => `${X(p.x)},${Y(p.y)}`).join(" ")}"/>`;
    pts.forEach((p) => { s += `<circle cx="${X(p.x)}" cy="${Y(p.y)}" r="${2.4 + Math.min(p.n || 1, 8) / 4}" fill="${se.color}"/>`; });
  });
  if (xLabel) s += `<text x="${W / 2}" y="${H - 3}" fill="#8a97ad" font-size="9" text-anchor="middle">${xLabel}</text>`;
  return s + `</svg>`;
}
// Barras verticales (histogramas)
function vbars(items, { color = "#00e08a", fmt = (v) => v, maxV } = {}) {
  const W = 300, H = 190, pad = 28, n = items.length, gap = 6;
  const max = maxV || Math.max(...items.map((i) => i.value), 1);
  const bw = (W - 2 * pad - gap * (n - 1)) / n;
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" class="vbars">`;
  s += `<line x1="${pad}" y1="${H - pad}" x2="${W - pad}" y2="${H - pad}" stroke="#243047"/>`;
  items.forEach((it, i) => {
    const h = (it.value / max) * (H - 2 * pad), x = pad + i * (bw + gap), y = H - pad - h;
    s += `<rect x="${x}" y="${y}" width="${bw}" height="${Math.max(0, h)}" rx="3" fill="${it.color || color}"/>`;
    s += `<text x="${x + bw / 2}" y="${H - pad + 12}" fill="#8a97ad" font-size="8" text-anchor="middle">${it.label}</text>`;
    s += `<text x="${x + bw / 2}" y="${y - 3}" fill="#cfd8e6" font-size="8.5" text-anchor="middle">${fmt(it.value)}</text>`;
  });
  return s + `</svg>`;
}
const MC = { elo: "#3b82f6", poisson: "#00e08a", ml: "#f5c542" };

let MODELS = [];
let SERVER_OFFSET = 0;
let nextMatchDate = null;

// ---------------- navegación ----------------
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    $("#" + btn.dataset.tab).classList.add("active");
    if (btn.dataset.tab === "standings") loadStandings();
    if (btn.dataset.tab === "teams") loadTeams();
    if (btn.dataset.tab === "calib") loadCalibration();
  });
});

// ---------------- reloj + cuenta atrás ----------------
function tick() {
  const now = new Date(Date.now() + SERVER_OFFSET);
  $("#clock").textContent = now.toLocaleTimeString("es-ES");
  if (nextMatchDate) {
    let diff = Math.max(0, nextMatchDate - now);
    const d = Math.floor(diff / 86400000); diff -= d * 86400000;
    const h = Math.floor(diff / 3600000); diff -= h * 3600000;
    const m = Math.floor(diff / 60000); diff -= m * 60000;
    const s = Math.floor(diff / 1000);
    const pad = (x) => String(x).padStart(2, "0");
    $("#countdown").textContent = (d > 0 ? d + "d " : "") + `${pad(h)}:${pad(m)}:${pad(s)}`;
  }
}
setInterval(tick, 1000);

// ---------------- estado / KPIs ----------------
const kpi = (v, l, cls) => `<div class="kpi ${cls}"><div class="v">${v}</div><div class="l">${l}</div></div>`;
async function loadStatus() {
  try {
    const s = await api("/api/status");
    SERVER_OFFSET = new Date(s.server_time) - new Date();
    $("#kpis").innerHTML = `
      ${kpi(s.teams, "Selecciones", "")}
      ${kpi(s.finished, "Jugados", "green")}
      ${kpi(s.scheduled, "Próximos", "")}
      ${kpi(s.in_play, "En juego", "gold")}`;
    $("#liveLabel").textContent = s.in_play > 0 ? `EN VIVO · ${s.in_play}` : "EN VIVO";
  } catch (e) { /* reintento en el próximo ciclo */ }
}

async function loadLive() {
  try {
    const d = await api("/api/live");
    SERVER_OFFSET = new Date(d.server_time) - new Date();

    // próximo partido + cuenta atrás
    if (d.next_match) {
      const n = d.next_match;
      nextMatchDate = n.utc_date ? new Date(n.utc_date) : null;
      $("#nextMatch").innerHTML = `${tf(n.home)} <span class="muted">vs</span> ${tf(n.away)}
        <div class="hint" style="margin-top:4px">${stageEs(n.stage)}${n.grp ? " · Grupo " + n.grp : ""} · ${fmtDate(n.utc_date)}</div>`;
    } else { $("#nextMatch").textContent = "Sin partidos programados."; nextMatchDate = null; $("#countdown").textContent = "—"; }

    // partido destacado
    const f = d.featured;
    $("#featuredMatch").innerHTML = f
      ? `${tf(f.home)} <span class="muted">vs</span> ${tf(f.away)}
         <div class="hint" style="margin-top:4px">${stageEs(f.stage)}${f.grp ? " · Grupo " + f.grp : ""} · ${fmtDate(f.utc_date)}</div>`
      : "—";

    // progreso del torneo
    const pr = d.progress || { played: 0, total: 0, pct: 0 };
    $("#progressWrap").innerHTML = `
      <div class="progress-head"><span>Progreso del torneo</span>
        <span><b>${pr.played}</b> de ${pr.total} partidos jugados · ${Math.round(pr.pct * 100)}%</span></div>
      <div class="progress-track"><span class="progress-fill" style="width:${Math.max(1.5, pr.pct * 100)}%"></span></div>`;

    // en juego
    $("#inPlay").innerHTML = d.in_play.length
      ? d.in_play.map((m) => `<div class="inplay-row"><span>${tf(m.home)} vs ${tf(m.away)}</span>
          <b class="live-score">${m.home_goals ?? 0} - ${m.away_goals ?? 0}</b></div>`).join("")
      : '<span class="muted">No hay partidos en juego en este momento.</span>';

    // últimos resultados
    $("#recentResults").innerHTML = (d.recent && d.recent.length)
      ? d.recent.map((m) => `<div class="inplay-row"><span>${tf(m.home)} vs ${tf(m.away)}</span>
          <b>${m.home_goals}-${m.away_goals}</b></div>`).join("")
      : '<span class="muted">Aún no hay partidos jugados.</span>';

    // próximos (lista compacta)
    $("#upcomingList").innerHTML = (d.upcoming && d.upcoming.length)
      ? d.upcoming.map((m) => `<div class="inplay-row"><span>${tf(m.home)} vs ${tf(m.away)}</span>
          <span class="hint">${fmtDate(m.utc_date)}</span></div>`).join("")
      : '<span class="muted">—</span>';

    // ticker
    const items = (d.upcoming || []).map((m) => `${esName(m.home)} vs ${esName(m.away)} · ${fmtDate(m.utc_date)}`);
    $("#tickerInner").textContent = "⚽ " + (items.length ? items.join("    •    ") : "Mundial 2026") + "    •    ";
  } catch {}
}

// Favoritos al título (simulación ligera, una vez al cargar)
async function loadFavorites() {
  try {
    const d = await api("/api/simulate?n=1000");
    const top = d.teams.slice(0, 5);
    $("#favorites").innerHTML = hbars(top.map((t) => ({
      label: esName(t.name), flag: flag(t.code, true), value: t.champion, color: COL.gold,
    })), { max: top[0] ? top[0].champion : 1, fmt: pct1 });
  } catch { $("#favorites").innerHTML = '<span class="muted">No disponible.</span>'; }
}

// ---------------- modelos ----------------
async function loadModels() {
  MODELS = await api("/api/models");
  const sel = $("#modelSelect"); sel.innerHTML = "";
  MODELS.filter((m) => m.kind === "match").forEach((m) => {
    const o = document.createElement("option"); o.value = m.key; o.textContent = m.name; sel.appendChild(o);
  });
  sel.addEventListener("change", () => { updateModelDesc(); loadPredictions(); });
  updateModelDesc();
}
function updateModelDesc() {
  const m = MODELS.find((x) => x.key === $("#modelSelect").value);
  $("#modelDesc").textContent = m ? m.desc : "";
}

// ---------------- predicciones ----------------
async function loadPredictions() {
  const model = $("#modelSelect").value, box = $("#predList");
  box.innerHTML = '<div class="spinner">Calculando predicciones…</div>';
  let preds = await api(`/api/predictions?model=${model}&status=SCHEDULED`);
  if (!preds.length) preds = await api(`/api/predictions?model=${model}&status=IN_PLAY`);
  if (!preds.length) { box.innerHTML = '<div class="spinner">No hay partidos próximos.</div>'; return; }
  box.innerHTML = ""; preds.forEach((p) => box.appendChild(predCard(p)));
}
function predCard(p) {
  const el = document.createElement("div"); el.className = "card pcard";
  const eh = esName(p.home), ea = esName(p.away);
  const parts = [
    { value: p.prob_home, color: COL.home, label: eh.length > 9 ? eh.slice(0, 8) + "…" : eh },
    { value: p.prob_draw, color: COL.draw, label: "Empate" },
    { value: p.prob_away, color: COL.away, label: ea.length > 9 ? ea.slice(0, 8) + "…" : ea },
  ];
  const xgMax = Math.max(p.expected_home_goals || 0, p.expected_away_goals || 0, 1.5);
  el.innerHTML = `
    <div class="meta">${stageEs(p.stage)}${p.grp ? " · Grupo " + p.grp : ""} · ${fmtDate(p.utc_date)}</div>
    <div class="teams"><span>${flag(p.home)}${eh}</span><span class="vs">vs</span><span>${ea}${flag(p.away)}</span></div>
    <div class="pcard-body">
      <div class="pdonut">${donut(parts)}</div>
      <div class="pinfo">
        <div class="scoreline">${p.most_likely_score ?? "—"}<small>marcador más probable</small></div>
        <div class="xg">
          <div class="xg-row"><span>${eh}</span><span class="xtrack"><span class="xfill" style="width:${((p.expected_home_goals||0)/xgMax*100)}%;background:${COL.home}"></span></span><b>${p.expected_home_goals ?? "?"}</b></div>
          <div class="xg-row"><span>${ea}</span><span class="xtrack"><span class="xfill" style="width:${((p.expected_away_goals||0)/xgMax*100)}%;background:${COL.away}"></span></span><b>${p.expected_away_goals ?? "?"}</b></div>
          <div class="xg-cap">goles esperados</div>
        </div>
      </div>
    </div>
    <div class="probrow">
      <span><i style="background:${COL.home}"></i>${pct1(p.prob_home)}</span>
      <span><i style="background:${COL.draw}"></i>${pct1(p.prob_draw)}</span>
      <span><i style="background:${COL.away}"></i>${pct1(p.prob_away)}</span>
    </div>
    <div class="extra">
      ${p.over_2_5 != null ? `<span>+2.5 goles: <b>${pct(p.over_2_5)}</b></span>` : ""}
      ${p.btts != null ? `<span>Ambos marcan: <b>${pct(p.btts)}</b></span>` : ""}
    </div>
    ${p.top_scores && p.top_scores.length ? `<div class="scores">${p.top_scores.slice(0,4).map((s)=>`<span class="schip"><b>${s.score}</b> ${pct(s.prob)}</span>`).join("")}</div>` : ""}
    ${p.note ? `<div class="note">ℹ️ ${p.note}</div>` : ""}`;
  return el;
}

// ---------------- clasificación ----------------
async function loadStandings() {
  const box = $("#standingsBox"); box.innerHTML = '<div class="spinner">Cargando…</div>';
  const data = await api("/api/standings"); box.innerHTML = "";
  Object.entries(data).forEach(([grp, rows]) => {
    const g = document.createElement("div"); g.className = "group";
    g.innerHTML = `<h3>Grupo ${grp}</h3>
      <table><thead><tr><th></th><th class="name" style="text-align:left">Equipo</th>
      <th>PJ</th><th>G</th><th>E</th><th>P</th><th>DG</th><th>Pts</th></tr></thead><tbody>
      ${rows.map((r,i)=>`<tr class="${i<2?"qual":""}"><td>${i+1}</td>
        <td class="name">${tfc(r.code, r.name)}</td>
        <td>${r.pj}</td><td>${r.g}</td><td>${r.e}</td><td>${r.p}</td>
        <td>${r.dg>0?"+"+r.dg:r.dg}</td><td class="pts">${r.pts}</td></tr>`).join("")}
      </tbody></table>`;
    box.appendChild(g);
  });
}

// ---------------- ratings (Elo) — 5 gráficos ----------------
async function loadTeams() {
  const box = $("#teamsBox"); box.innerHTML = '<div class="spinner">Cargando…</div>';
  const teams = await api("/api/teams");
  const byElo = [...teams].sort((a, b) => b.elo - a.elo);
  const minElo = Math.min(...teams.map((t) => t.elo)) - 30;

  // 1) Top-16 Elo
  const eloChart = hbars(byElo.slice(0, 16).map((t) => ({
    label: esName(t.name), flag: flag(t.code, true), value: t.elo - minElo,
    color: `hsl(${Math.max(0, (t.elo - 1600) / 6)} 70% 48%)`,
  })), { fmt: (v) => Math.round(v + minElo) });

  // 2) Mejor ataque
  const atkMax = Math.max(...teams.map((t) => t.attack));
  const atkChart = hbars([...teams].sort((a, b) => b.attack - a.attack).slice(0, 12).map((t) => ({
    label: esName(t.name), flag: flag(t.code, true), value: t.attack, color: COL.away,
  })), { max: atkMax, fmt: (v) => v.toFixed(2) });

  // 3) Solidez defensiva (menor 'defensa' = mejor)
  const defMin = Math.min(...teams.map((t) => t.defense));
  const defChart = hbars([...teams].sort((a, b) => a.defense - b.defense).slice(0, 12).map((t) => ({
    label: esName(t.name), flag: flag(t.code, true), value: 2 - t.defense, color: COL.home,
  })), { max: 2 - defMin, fmt: (v) => (2 - v).toFixed(2) });

  // 4) Elo medio por grupo
  const groups = {};
  teams.forEach((t) => { (groups[t.grp] = groups[t.grp] || []).push(t.elo); });
  const gBase = 1550;
  const grpChart = hbars(Object.entries(groups).map(([g, arr]) => ({
    label: "Grupo " + g, value: arr.reduce((a, b) => a + b, 0) / arr.length - gBase, color: COL.green,
  })).sort((a, b) => b.value - a.value), { fmt: (v) => Math.round(v + gBase) });

  // 5) Distribución de Elo
  const ranges = [["<1700", 0], ["1700–1800", 0], ["1800–1900", 0], ["1900–2000", 0], ["2000+", 0]];
  teams.forEach((t) => {
    const e = t.elo;
    const i = e < 1700 ? 0 : e < 1800 ? 1 : e < 1900 ? 2 : e < 2000 ? 3 : 4;
    ranges[i][1]++;
  });
  const distChart = vbars(ranges.map((r) => ({ label: r[0], value: r[1] })), { color: COL.gold });

  box.innerHTML = `
    <div class="chart-grid">
      ${chartCard("🏅 Top 16 · rating Elo", "fuerza global de cada selección", eloChart, "wide")}
      ${chartCard("⚔️ Mejor ataque", "factor de ataque (1.00 = media)", atkChart)}
      ${chartCard("🛡️ Solidez defensiva", "menos goles esperados en contra", defChart)}
      ${chartCard("👥 Elo medio por grupo", "grupos ordenados por nivel medio", grpChart)}
      ${chartCard("📈 Distribución de Elo", "nº de selecciones por nivel", distChart)}
    </div>
    <h3 class="section-title">Tabla completa</h3>
    <table><thead><tr><th>#</th><th class="name" style="text-align:left">Selección</th>
    <th>Grupo</th><th>Elo</th><th>Ataque</th><th>Defensa</th></tr></thead><tbody>
    ${byElo.map((t,i)=>`<tr><td>${i+1}</td><td class="name">${tfc(t.code,t.name)}</td>
      <td>${t.grp||"—"}</td><td><b>${Math.round(t.elo)}</b></td>
      <td>${t.attack.toFixed(2)}</td><td>${t.defense.toFixed(2)}</td></tr>`).join("")}
    </tbody></table>
    <p class="hint" style="margin-top:10px">Ataque/Defensa: 1.00 = media del torneo. Ataque &gt;1 marca más; Defensa &gt;1 encaja más.</p>`;
}

// ---------------- simulación Monte Carlo ----------------
$("#simBtn").addEventListener("click", runSim);
async function runSim() {
  const n = $("#simN").value, base = $("#simBase").value;
  $("#simStatus").textContent = `Simulando ${(+n).toLocaleString("es-ES")} torneos…`;
  $("#simBox").innerHTML = '<div class="spinner">Ejecutando simulaciones…</div>';
  const data = await api(`/api/simulate?n=${n}&base=${base}`);
  $("#simStatus").textContent = `${data.sims.toLocaleString("es-ES")} simulaciones · base ${data.base_model}`;
  const rows = data.teams.filter((t)=>t.qualify>0.001||t.champion>0.001);
  const top3 = data.teams.slice(0, 3);

  const podium = `<div class="podium">${[1,0,2].map((idx)=>{
    const t = top3[idx]; if(!t) return ""; const pos = idx+1;
    return `<div class="pod pod${pos}">
      <div class="pod-medal">${pos===1?"🥇":pos===2?"🥈":"🥉"}</div>
      <div class="pod-flag">${flag(t.code,true)||"🏳️"}</div>
      <div class="pod-name">${esName(t.name)}</div>
      <div class="pod-pct">${pct1(t.champion)}</div>
      <div class="pod-bar"></div></div>`;
  }).join("")}</div>`;

  const champBars = hbars(data.teams.slice(0, 12).map((t)=>({
    label: esName(t.name), flag: flag(t.code, true), value: t.champion, color: COL.gold,
  })), { fmt: pct1 });

  const table = `<table><thead><tr><th>#</th><th class="name" style="text-align:left">Selección</th>
    <th>Gana grupo</th><th>Clasifica</th><th>Cuartos</th><th>Semis</th><th>Final</th><th>🏆 Campeón</th></tr></thead><tbody>
    ${rows.map((t,i)=>`<tr><td>${i+1}</td><td class="name">${tfc(t.code,t.name)}</td>
      <td>${cell(t.win_group)}</td><td>${cell(t.qualify)}</td><td>${cell(t.qf)}</td>
      <td>${cell(t.sf)}</td><td>${cell(t.final)}</td>
      <td class="champ">${pct1(t.champion)}</td></tr>`).join("")}
    </tbody></table>`;

  $("#simBox").innerHTML = podium +
    `<h3 class="section-title">🏆 Probabilidad de ser campeón (top 12)</h3>${champBars}` +
    `<h3 class="section-title">Detalle por ronda</h3>${table}`;
}
function cell(v) {
  const w = Math.round((v || 0) * 100);
  return `<span class="cellbar"><span class="cellfill" style="width:${w}%"></span><span class="cellnum">${pct(v)}</span></span>`;
}

// ---------------- calibración (10 gráficos) ----------------
let calibLoaded = false;
$("#calibBtn").addEventListener("click", () => loadCalibration(true));
async function loadCalibration(force) {
  if (calibLoaded && !force) return;
  $("#calibCards").innerHTML = '<div class="spinner">Validando modelos (walk-forward)…</div>';
  $("#calibCharts").innerHTML = "";
  const d = await api("/api/evaluation");
  calibLoaded = true;
  $("#calibDataset").textContent = `${d.dataset} · ${d.n_matches} partidos`;
  const names = { elo: "Elo", poisson: "Poisson", ml: "Aprendizaje automático" };
  const order = ["elo", "poisson", "ml"];
  const best = order.reduce((b, k) => (d.models[k].rps < d.models[b].rps ? k : b), "elo");

  // tarjetas resumen
  $("#calibCards").innerHTML = order.map((k) => {
    const m = d.models[k];
    return `<div class="metric-card ${k===best?"best":""}">
      <h4>${names[k]} ${k===best?'<span class="tag">★ mejor RPS</span>':""}</h4>
      <div class="metric-row"><span>Precisión</span><span class="mv">${pct1(m.accuracy)}</span></div>
      <div class="metric-row"><span>Log-loss <span class="hint">(↓)</span></span><span class="mv">${m.log_loss}</span></div>
      <div class="metric-row"><span>Brier <span class="hint">(↓)</span></span><span class="mv">${m.brier}</span></div>
      <div class="metric-row"><span>RPS <span class="hint">(↓)</span></span><span class="mv">${m.rps}</span></div>
    </div>`;
  }).join("") + `<div class="metric-card ref">
      <h4>Referencia</h4>
      <div class="metric-row"><span>Azar (1/X/2) log-loss</span><span class="mv">${d.baseline.log_loss_uniforme}</span></div>
      <div class="metric-row"><span>Clase mayoritaria</span><span class="mv">${pct1(d.baseline.accuracy_mayoritaria)}</span></div>
      <div class="metric-row"><span>Muestra</span><span class="mv">${d.n_matches}</span></div>
    </div>`;

  // métricas derivadas por modelo (a partir de los tramos de fiabilidad)
  const baseLL = d.baseline.log_loss_uniforme;
  const der = {};
  order.forEach((k) => {
    const bins = (d.models[k].reliability || []).filter((b) => b.n > 0);
    const N = bins.reduce((a, b) => a + b.n, 0) || 1;
    der[k] = {
      bins,
      calibErr: bins.reduce((a, b) => a + Math.abs(b.conf - b.acc) * b.n, 0) / N,
      sharp: bins.reduce((a, b) => a + b.conf * b.n, 0) / N,
      skill: (baseLL - d.models[k].log_loss) / baseLL,
    };
  });

  const cc = (k) => (k === best ? COL.green : MC[k]);
  const bars = (valfn, fmt, max) => hbars(order.map((k) => ({ label: names[k], value: valfn(k), color: cc(k) })), { max, fmt });
  const f3 = (v) => v.toFixed(3);
  const leg = legend(order.map((k) => ({ label: names[k], color: MC[k] })));
  const relSeries = order.map((k) => ({ color: MC[k], points: der[k].bins.map((b) => ({ x: b.conf, y: b.acc, n: b.n })) }));
  const gapSeries = order.map((k) => ({ color: MC[k], points: der[k].bins.map((b) => ({ x: b.conf, y: b.conf - b.acc, n: b.n })) }));
  const histo = der[best].bins.map((b) => ({ label: b.conf.toFixed(1), value: b.n }));
  const maxSkill = Math.max(...order.map((k) => der[k].skill), 0.01);

  $("#calibCharts").innerHTML = [
    chartCard("Precisión", "acierto del 1/X/2 — mayor es mejor", bars((k) => d.models[k].accuracy, pct1, 1)),
    chartCard("Log-loss", `menor es mejor · azar = ${baseLL}`, bars((k) => d.models[k].log_loss, f3, baseLL * 1.1)),
    chartCard("Brier score", "error cuadrático — menor es mejor", bars((k) => d.models[k].brier, f3)),
    chartCard("RPS", "puntuación de probabilidad ordenada — menor es mejor", bars((k) => d.models[k].rps, f3)),
    chartCard("Habilidad vs azar", "mejora del log-loss frente al azar", bars((k) => der[k].skill, pct1, maxSkill)),
    chartCard("Error de calibración", "desvío medio confianza–acierto — menor es mejor", bars((k) => der[k].calibErr, f3)),
    chartCard("Nitidez (confianza media)", "cuán decididas son las predicciones", bars((k) => der[k].sharp, pct1, 1)),
    chartCard("Diagrama de fiabilidad", "confianza vs acierto; la diagonal = perfecto", lineChart(relSeries, { diagonal: true, xLabel: "Confianza prevista" }) + leg),
    chartCard("Gap de calibración", "confianza − acierto por tramo; 0 = perfecto", lineChart(gapSeries, { yRange: [-0.4, 0.4], zero: true, xLabel: "Confianza prevista" }) + leg),
    chartCard("Distribución de confianza", `predicciones por nivel (modelo ${names[best]})`, vbars(histo, { color: COL.green })),
  ].join("");
  $("#tipsList").innerHTML = d.tips.map((t) => `<li>${t}</li>`).join("");
}

// ---------------- actualizar ----------------
$("#refreshBtn").addEventListener("click", async () => {
  const btn = $("#refreshBtn"); btn.textContent = "Actualizando…"; btn.disabled = true;
  try { await fetch("/api/refresh", { method: "POST" }); await loadStatus(); await loadLive(); await loadPredictions(); calibLoaded = false; }
  finally { btn.textContent = "⟳ Actualizar datos"; btn.disabled = false; }
});

// ---------------- init ----------------
(async function init() {
  NAME2CODE = {};
  try { (await api("/api/teams")).forEach((t) => { NAME2CODE[t.name] = t.code; }); } catch {}
  await loadStatus();
  await loadLive();
  loadFavorites();
  await loadModels();
  await loadPredictions();
  tick();
  setInterval(loadStatus, 30000);
  setInterval(loadLive, 20000);
})();
