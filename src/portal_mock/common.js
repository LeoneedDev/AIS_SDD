const API = {
  auth: "/api/customer_portal",
  orders: "/api/order_orchestrator/orders",
  ws: "/api/modeling_workspace",
  repo: "/api/model_repository",
  val: "/api/model_validator",
};

const PRINT_LABELS = {
  not_ready: "Pripravuje sa",
  ready_for_print: "Pripravené na tlač",
  printing: "V tlači",
  cannot_be_fulfilled: "Nedá sa vykonať",
};
const STATE_LABELS = {
  waiting_for_review: "Čaká na zákazníka",
  in_review: "Zákazník posudzuje",
  approved: "Schválené zákazníkom",
  rejected: "Zákazník nesúhlasí",
  closed_new_development: "Nový platený vývoj",
};
const PATH_LABELS = { "VAR-1": "Model vytvoríme my", "VAR-2": "Vlastný model zákazníka" };

const $ = (id) => document.getElementById(id);

function log(label, status, body) {
  const el = $("log");
  if (el) el.textContent = `${label} → ${status}\n${JSON.stringify(body, null, 2)}\n\n` + el.textContent;
}

async function api(method, url, body, isForm) {
  const headers = { "X-Correlation-ID": crypto.randomUUID() };
  if (body && !isForm) headers["Content-Type"] = "application/json";
  const res = await fetch(url, { method, headers, body: isForm ? body : body ? JSON.stringify(body) : undefined });
  if (res.status === 401) { location.replace("login.html"); return { ok: false, status: 401, data: {} }; }
  const data = res.status === 204 ? {} : await res.json().catch(() => ({}));
  log(`${method} ${url}`, res.status, data);
  return { ok: res.ok, status: res.status, data };
}

async function requireSession(allowedRoles) {
  const r = await fetch(`${API.auth}/sessions/current`);
  if (!r.ok) { location.replace("login.html"); return null; }
  const s = await r.json();
  if (!allowedRoles.includes(s.role)) { location.replace(s.role === "customer" ? "index.html" : "modeler.html"); return null; }
  $("who").textContent = s.nickname ? `${s.nickname} (${s.role})` : `${s.account_id} (${s.role})`;
  $("logout").onclick = async () => {
    await fetch(`${API.auth}/sessions/current`, { method: "DELETE" });
    location.replace("login.html");
  };
  return s;
}

function badge(cls, text) {
  const b = document.createElement("span");
  b.className = `badge ${cls}`;
  b.textContent = text;
  return b;
}

function renderHistory(el, approval) {
  el.innerHTML = "";
  for (const h of approval.history) {
    const li = document.createElement("li");
    const who = h.employee ? `${h.employee.nickname} (ID ${h.employee.employee_id})` : "zákazník";
    li.textContent = `${new Date(h.occurred_at).toLocaleString()} – ${h.event} – ${who}${h.comment ? ": " + h.comment : ""}`;
    el.appendChild(li);
  }
}

function renderOrders(el, orders, selectedId, onSelect, extra) {
  el.innerHTML = "";
  if (!orders.length) { el.innerHTML = '<li class="empty">Zatiaľ žiadne objednávky.</li>'; return; }
  for (const o of orders) {
    const li = document.createElement("li");
    if (o.order_id === selectedId) li.className = "active";
    const title = document.createElement("div");
    title.className = "title";
    title.textContent = o.description;
    const meta = document.createElement("div");
    meta.className = "meta";
    const left = document.createElement("span");
    left.textContent = `${PATH_LABELS[o.path]} · ${new Date(o.created_at).toLocaleDateString()}` + (extra ? extra(o) : "");
    meta.append(left, badge(o.print_status, PRINT_LABELS[o.print_status]));
    li.append(title, meta);
    li.onclick = () => onSelect(o);
    el.appendChild(li);
  }
}
