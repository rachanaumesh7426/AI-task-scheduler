/* app.js — Cloud Task Scheduler frontend */

// ─── State ────────────────────────────────────────────────────
let state = {
  tasks: [],
  servers: [],
  lastResults: null,
  editMode: null,   // { type: 'task'|'server', index: number|null }
};

// ─── Demo data ────────────────────────────────────────────────
const DEMO = {
  tasks: [
    { name: "GPT-Infer-1",  workload: 10, sensitivity: 5, priority: 3, task_type: "inference" },
    { name: "BatchJob-2",   workload: 15, sensitivity: 2, priority: 1, task_type: "batch" },
    { name: "Train-ResNet", workload: 25, sensitivity: 3, priority: 2, task_type: "training" },
    { name: "API-Request",  workload: 5,  sensitivity: 4, priority: 3, task_type: "inference" },
    { name: "DataPipeline", workload: 18, sensitivity: 1, priority: 1, task_type: "batch" },
    { name: "SecureInfer",  workload: 8,  sensitivity: 5, priority: 3, task_type: "inference" },
  ],
  servers: [
    { name: "Alpha", speed: 8,  security: 5, capacity: 50, compromised: false, region: "us-east" },
    { name: "Beta",  speed: 12, security: 2, capacity: 60, compromised: false, region: "us-west" },
    { name: "Gamma", speed: 5,  security: 4, capacity: 40, compromised: true,  region: "eu-central" },
    { name: "Delta", speed: 10, security: 3, capacity: 55, compromised: false, region: "ap-south" },
  ],
};

// ─── Render helpers ───────────────────────────────────────────
function sensBadge(v) {
  return `<span class="badge badge-sens">S:${v}</span>`;
}
function secBadge(v) {
  return `<span class="badge badge-sec">🔒${v}</span>`;
}
function typeBadge(v) {
  return `<span class="badge badge-type">${v}</span>`;
}
function compBadge() {
  return `<span class="badge badge-comp">⚠ COMPROMISED</span>`;
}

function renderTasks() {
  const el = document.getElementById("tasks-list");
  if (state.tasks.length === 0) {
    el.innerHTML = `<div style="color:var(--fg2);font-size:.75rem;padding:.8rem 0;">No tasks yet.</div>`;
    return;
  }
  el.innerHTML = state.tasks.map((t, i) => `
    <div class="entity-row">
      <div class="entity-main">
        <span class="entity-name">${t.name}</span>
        <span class="entity-meta">workload: ${t.workload} · priority: ${t.priority}</span>
      </div>
      <div class="entity-badges">
        ${sensBadge(t.sensitivity)} ${typeBadge(t.task_type)}
        <button class="btn btn-sm btn-ghost" onclick="editTask(${i})">✎</button>
        <button class="btn btn-sm btn-danger" onclick="removeTask(${i})">✕</button>
      </div>
    </div>
  `).join("");
}

function renderServers() {
  const el = document.getElementById("servers-list");
  if (state.servers.length === 0) {
    el.innerHTML = `<div style="color:var(--fg2);font-size:.75rem;padding:.8rem 0;">No servers yet.</div>`;
    return;
  }
  el.innerHTML = state.servers.map((s, i) => `
    <div class="entity-row">
      <div class="entity-main">
        <span class="entity-name">${s.name}</span>
        <span class="entity-meta">speed: ${s.speed} · cap: ${s.capacity} · ${s.region}</span>
      </div>
      <div class="entity-badges">
        ${secBadge(s.security)}
        ${s.compromised ? compBadge() : ""}
        <button class="btn btn-sm btn-ghost" onclick="editServer(${i})">✎</button>
        <button class="btn btn-sm btn-danger" onclick="removeServer(${i})">✕</button>
      </div>
    </div>
  `).join("");
}

function renderAll() { renderTasks(); renderServers(); }

// ─── CRUD ─────────────────────────────────────────────────────
window.removeTask   = (i) => { state.tasks.splice(i, 1); renderTasks(); };
window.removeServer = (i) => { state.servers.splice(i, 1); renderServers(); };
window.editTask     = (i) => openModal("task", i);
window.editServer   = (i) => openModal("server", i);

// ─── Modal ────────────────────────────────────────────────────
const overlay = document.getElementById("modal-overlay");
const modalTitle = document.getElementById("modal-title");
const modalBody  = document.getElementById("modal-body");

function taskForm(t = {}) {
  return `
    <div class="form-row"><label>Name</label>
      <input id="f-name" value="${t.name||""}" placeholder="Task-1" /></div>
    <div class="form-row"><label>Workload (compute units)</label>
      <input id="f-workload" type="number" min="0.1" step="0.1" value="${t.workload||10}" /></div>
    <div class="form-row"><label>Sensitivity (1–5)</label>
      <input id="f-sensitivity" type="number" min="1" max="5" value="${t.sensitivity||3}" /></div>
    <div class="form-row"><label>Priority (1–3)</label>
      <input id="f-priority" type="number" min="1" max="3" value="${t.priority||1}" /></div>
    <div class="form-row"><label>Type</label>
      <select id="f-type">
        ${["inference","training","batch"].map(tp =>
          `<option value="${tp}" ${(t.task_type||"inference")===tp?"selected":""}>${tp}</option>`
        ).join("")}
      </select>
    </div>
  `;
}

function serverForm(s = {}) {
  return `
    <div class="form-row"><label>Name</label>
      <input id="f-name" value="${s.name||""}" placeholder="Server-A" /></div>
    <div class="form-row"><label>Speed (compute/time)</label>
      <input id="f-speed" type="number" min="0.1" step="0.1" value="${s.speed||5}" /></div>
    <div class="form-row"><label>Security level (1–5)</label>
      <input id="f-security" type="number" min="1" max="5" value="${s.security||3}" /></div>
    <div class="form-row"><label>Capacity (max workload)</label>
      <input id="f-capacity" type="number" min="1" step="1" value="${s.capacity||50}" /></div>
    <div class="form-row"><label>Region</label>
      <select id="f-region">
        ${["us-east","us-west","eu-central","ap-south"].map(r =>
          `<option value="${r}" ${(s.region||"us-east")===r?"selected":""}>${r}</option>`
        ).join("")}
      </select>
    </div>
    <div class="form-row form-inline">
      <label class="form-checkbox">
        <input id="f-compromised" type="checkbox" ${s.compromised?"checked":""} />
        <span style="font-size:.8rem;color:var(--danger)">⚠ Mark as compromised</span>
      </label>
    </div>
  `;
}

function openModal(type, index = null) {
  state.editMode = { type, index };
  const isTask = type === "task";
  const existing = index !== null
    ? (isTask ? state.tasks[index] : state.servers[index])
    : {};
  modalTitle.textContent = `${index !== null ? "Edit" : "Add"} ${isTask ? "Task" : "Server"}`;
  modalBody.innerHTML = isTask ? taskForm(existing) : serverForm(existing);
  overlay.classList.remove("hidden");
}

function closeModal() {
  overlay.classList.add("hidden");
  state.editMode = null;
}

function saveModal() {
  const { type, index } = state.editMode;
  if (type === "task") {
    const obj = {
      name:        document.getElementById("f-name").value.trim() || `Task-${Date.now()}`,
      workload:    parseFloat(document.getElementById("f-workload").value),
      sensitivity: parseInt(document.getElementById("f-sensitivity").value),
      priority:    parseInt(document.getElementById("f-priority").value),
      task_type:   document.getElementById("f-type").value,
    };
    if (index !== null) state.tasks[index] = obj;
    else state.tasks.push(obj);
    renderTasks();
  } else {
    const obj = {
      name:        document.getElementById("f-name").value.trim() || `Server-${Date.now()}`,
      speed:       parseFloat(document.getElementById("f-speed").value),
      security:    parseInt(document.getElementById("f-security").value),
      capacity:    parseFloat(document.getElementById("f-capacity").value),
      region:      document.getElementById("f-region").value,
      compromised: document.getElementById("f-compromised").checked,
    };
    if (index !== null) state.servers[index] = obj;
    else state.servers.push(obj);
    renderServers();
  }
  closeModal();
}

document.getElementById("modal-close").addEventListener("click", closeModal);
document.getElementById("modal-cancel").addEventListener("click", closeModal);
document.getElementById("modal-save").addEventListener("click", saveModal);
overlay.addEventListener("click", e => { if (e.target === overlay) closeModal(); });

// ─── Load data buttons ────────────────────────────────────────
document.getElementById("btn-demo").addEventListener("click", () => {
  state.tasks   = JSON.parse(JSON.stringify(DEMO.tasks));
  state.servers = JSON.parse(JSON.stringify(DEMO.servers));
  renderAll();
  setStatus("Demo scenario loaded.", "ok");
});

document.getElementById("btn-random").addEventListener("click", async () => {
  setStatus("Fetching random scenario…", "loading");
  try {
    const r = await fetch(`/api/random?tasks=7&servers=4`);
    const d = await r.json();
    state.tasks   = d.tasks;
    state.servers = d.servers;
    renderAll();
    setStatus(`Random scenario loaded (seed ${d.seed}).`, "ok");
  } catch (e) {
    setStatus("Failed to load random scenario.", "err");
  }
});

document.getElementById("btn-add-task").addEventListener("click", () => openModal("task"));
document.getElementById("btn-add-server").addEventListener("click", () => openModal("server"));

// ─── Sliders ──────────────────────────────────────────────────
["w1","w2","w3"].forEach(id => {
  const slider = document.getElementById(id);
  const display = document.getElementById(`${id}-val`);
  slider.addEventListener("input", () => { display.textContent = parseFloat(slider.value).toFixed(1); });
});

// ─── Run scheduler ───────────────────────────────────────────
document.getElementById("btn-run").addEventListener("click", async () => {
  if (!state.tasks.length || !state.servers.length) {
    setStatus("Add at least one task and one server.", "err"); return;
  }
  setStatus("Running optimisation…", "loading");

  const payload = {
    tasks: state.tasks,
    servers: state.servers,
    weights: {
      w1: parseFloat(document.getElementById("w1").value),
      w2: parseFloat(document.getElementById("w2").value),
      w3: parseFloat(document.getElementById("w3").value),
    },
  };

  try {
    const r = await fetch("/api/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const d = await r.json();
    if (d.status !== "ok") throw new Error(d.message);

    state.lastResults = d;
    renderResults(d);
    renderCharts(d.charts);
    document.getElementById("results").classList.remove("hidden");
    document.getElementById("charts").classList.remove("hidden");
    document.getElementById("results").scrollIntoView({ behavior: "smooth" });
    setStatus(`Done. Improvement: ${d.improvement_pct}%`, "ok");
  } catch (e) {
    setStatus(`Error: ${e.message}`, "err");
  }
});

// ─── Results rendering ────────────────────────────────────────
function renderResults(d) {
  document.getElementById("kpi-naive").textContent = d.naive.total_cost.toFixed(2);
  document.getElementById("kpi-opt").textContent   = d.optimized.total_cost.toFixed(2);
  document.getElementById("kpi-impr").textContent  = `${d.improvement_pct}%`;

  document.getElementById("table-naive").innerHTML = assignmentTable(d.naive.assignments);
  document.getElementById("table-opt").innerHTML   = assignmentTable(d.optimized.assignments);
}

function assignmentTable(rows) {
  if (!rows || !rows.length) return "<p style='color:var(--fg2);font-size:.75rem;'>No assignments.</p>";
  const head = `<tr>
    <th>Task</th><th>Server</th><th>Time</th><th>Risk</th><th>Load</th><th>Total</th>
  </tr>`;
  const body = rows.map(r => {
    const comp = r.server_compromised ? " comp-row" : "";
    return `<tr class="${comp}">
      <td>${r.task_name}</td>
      <td>${r.server_name}${r.server_compromised ? " ⚠" : ""}</td>
      <td>${r.time_cost.toFixed(2)}</td>
      <td class="${r.risk_penalty > 0 ? "risk-cell" : ""}">${r.risk_penalty.toFixed(2)}</td>
      <td>${r.load_penalty.toFixed(3)}</td>
      <td><strong>${r.total_cost.toFixed(2)}</strong></td>
    </tr>`;
  }).join("");
  return `<table><thead>${head}</thead><tbody>${body}</tbody></table>`;
}

// ─── Charts ───────────────────────────────────────────────────
function renderCharts(charts) {
  if (!charts) return;
  document.getElementById("chart-breakdown").src = `data:image/png;base64,${charts.cost_breakdown}`;
  document.getElementById("chart-total").src      = `data:image/png;base64,${charts.total_cost}`;
  document.getElementById("chart-util").src       = `data:image/png;base64,${charts.server_utilisation}`;
  document.getElementById("chart-heat").src       = `data:image/png;base64,${charts.risk_heatmap}`;
}

// ─── Export ───────────────────────────────────────────────────
async function exportFile(format) {
  if (!state.lastResults) { alert("Run the scheduler first."); return; }
  const payload = {
    tasks: state.tasks, servers: state.servers,
    weights: {
      w1: parseFloat(document.getElementById("w1").value),
      w2: parseFloat(document.getElementById("w2").value),
      w3: parseFloat(document.getElementById("w3").value),
    },
  };
  try {
    const r = await fetch(`/api/export/${format}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `schedule_results.${format}`;
    document.body.appendChild(a); a.click();
    URL.revokeObjectURL(url); a.remove();
  } catch (e) {
    alert(`Export failed: ${e.message}`);
  }
}

document.getElementById("btn-export-csv").addEventListener("click", () => exportFile("csv"));
document.getElementById("btn-export-json").addEventListener("click", () => exportFile("json"));

// ─── Batch simulation ────────────────────────────────────────
document.getElementById("btn-batch").addEventListener("click", async () => {
  const runs    = document.getElementById("batch-runs").value;
  const tasks   = document.getElementById("batch-tasks").value;
  const servers = document.getElementById("batch-servers").value;
  const el = document.getElementById("batch-results");
  el.innerHTML = `<div style="color:var(--fg2);font-size:.75rem;">Running ${runs} simulations…</div>`;
  el.classList.remove("hidden");

  try {
    const r = await fetch(`/api/batch?runs=${runs}&tasks=${tasks}&servers=${servers}`);
    const d = await r.json();
    if (d.status !== "ok") throw new Error("Batch failed");
    const labels = {
      num_runs: "Runs",
      avg_naive_cost: "Avg Naive Cost",
      avg_opt_cost: "Avg Optimised Cost",
      avg_improvement_pct: "Avg Improvement %",
      max_improvement_pct: "Max Improvement %",
      min_improvement_pct: "Min Improvement %",
      stddev_improvement: "Std Dev Improvement",
    };
    el.innerHTML = Object.entries(d.stats).map(([k, v]) => `
      <div class="batch-stat">
        <div class="batch-stat-key">${labels[k] || k}</div>
        <div class="batch-stat-val">${typeof v === "number" ? v.toFixed(2) : v}</div>
      </div>
    `).join("");
  } catch (e) {
    el.innerHTML = `<div style="color:var(--danger)">Error: ${e.message}</div>`;
  }
});

// ─── Status helper ────────────────────────────────────────────
function setStatus(msg, cls = "") {
  const el = document.getElementById("run-status");
  el.textContent = msg;
  el.className = `run-status ${cls}`;
}

// ─── Init ─────────────────────────────────────────────────────
(function init() {
  state.tasks   = JSON.parse(JSON.stringify(DEMO.tasks));
  state.servers = JSON.parse(JSON.stringify(DEMO.servers));
  renderAll();
})();
