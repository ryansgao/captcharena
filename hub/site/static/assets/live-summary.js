// CAPTCHArena: fills #live-summary from the measurement service's aggregate JSON when it exists.
// Without result rows (warm-up, 404, network error, CORS, bad JSON) the static warm-up text already in the page stays as is.
// Builds DOM nodes with textContent only: nothing from the response is ever parsed as HTML.
(function () {
  "use strict";
  var box = document.getElementById("live-summary");
  if (!box || !window.fetch) return;
  var src = box.getAttribute("data-src");
  var out = box.querySelector(".result");
  if (!src || !out) return;

  function el(tag, text) { var n = document.createElement(tag); if (text !== undefined) n.textContent = String(text); return n; }
  function fmt(v) {
    if (v === null || v === undefined) return "—";
    if (typeof v === "number") return Number.isInteger(v) ? v.toLocaleString("en") : v.toFixed(3).replace(/\.?0+$/, "");
    if (typeof v === "object") return JSON.stringify(v);
    return String(v);
  }
  function label(k) { return String(k).replace(/_/g, " "); }

  // Lanes may arrive as an array of objects or as an object keyed by lane name.
  function laneRows(lanes) {
    if (Array.isArray(lanes)) return lanes.filter(function (r) { return r && typeof r === "object"; });
    if (lanes && typeof lanes === "object") {
      return Object.keys(lanes).map(function (k) {
        var r = lanes[k]; var row = { lane: k };
        if (r && typeof r === "object") Object.keys(r).forEach(function (c) { row[c] = r[c]; }); else row.value = r;
        return row;
      });
    }
    return [];
  }

  function table(rows) {
    var cols = [];
    rows.forEach(function (r) { Object.keys(r).forEach(function (c) { if (cols.indexOf(c) < 0) cols.push(c); }); });
    var t = el("table"), thead = el("thead"), tr = el("tr"), tbody = el("tbody");
    cols.forEach(function (c) { var th = el("th", label(c)); th.scope = "col"; tr.appendChild(th); });
    thead.appendChild(tr); t.appendChild(thead);
    rows.forEach(function (r) {
      var row = el("tr");
      cols.forEach(function (c) { row.appendChild(el("td", fmt(r[c]))); });
      tbody.appendChild(row);
    });
    t.appendChild(tbody);
    return t;
  }

  // Renders only when the feed carries result rows. A feed with metadata but no rows (the warm-up) keeps the
  // static warm-up text, so visitors never see bare field names.
  function render(data) {
    var rows = laneRows(data.lanes || data.by_lane || data.results || data.rows);
    if (!rows.length) return false;
    var frag = document.createDocumentFragment();
    var when = data.generated_at || data.generated || data.updated_at || data.as_of || data.time;
    var head = el("p", "Live from the measurement service" + (when ? ", generated " + fmt(when) : "") + ".");
    head.className = "meta";
    frag.appendChild(head);
    if (data.note || data.message) frag.appendChild(el("p", data.note || data.message));
    frag.appendChild(table(rows));
    out.textContent = "";
    out.appendChild(frag);
    return true;
  }

  box.setAttribute("data-state", "loading");
  var ctrl = window.AbortController ? new AbortController() : null;
  var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, 8000) : null;
  fetch(src, { credentials: "omit", mode: "cors", cache: "no-store", signal: ctrl ? ctrl.signal : undefined })
    .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then(function (data) {
      if (!data || typeof data !== "object" || Array.isArray(data) || !render(data)) throw new Error("empty");
      box.setAttribute("data-state", "live");
    })
    .catch(function () { box.setAttribute("data-state", "pending"); })
    .then(function () { if (timer) clearTimeout(timer); });
})();
