// Minimal widget for the lab's open-source CAPTCHAs (interactions modelled on go-captcha-jslib; same gc-* names).
const type = document.body.dataset.type;
const box = document.getElementById("lab");
const v = document.getElementById("lab-verdict");
const el = (tag, attrs = {}, kids = []) => { const e = document.createElement(tag); Object.assign(e, attrs); kids.forEach(k => e.appendChild(k)); return e; };

async function submit(key, value) {
  document.body.dataset.state = "checking";
  const r = await (await fetch("/api/check", { method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ type, key, value: String(value), client: navigator.userAgent }) })).json();
  document.body.dataset.verdict = r.ok ? "pass" : "fail";
  v.textContent = r.ok ? "accepted by its server" : "rejected by its server; a new challenge follows";
  v.className = "verdict " + (r.ok ? "pass" : "fail");
  if (!r.ok) setTimeout(load, 1000);
  else document.body.dataset.state = "done";
}

function dragger(handle, onMove, onUp) {
  handle.addEventListener("pointerdown", e => {
    e.preventDefault(); handle.setPointerCapture(e.pointerId);
    const x0 = e.clientX, y0 = e.clientY;
    const mv = ev => onMove(ev.clientX - x0, ev.clientY - y0);
    const up = ev => { handle.removeEventListener("pointermove", mv); handle.removeEventListener("pointerup", up); onUp(ev.clientX - x0, ev.clientY - y0); };
    handle.addEventListener("pointermove", mv); handle.addEventListener("pointerup", up);
  });
}

function textWidget(d) {
  const inp = el("input", { id: "captcha-answer", name: "captcha", autocomplete: "off", placeholder: "characters" });
  const btn = el("button", { id: "captcha-submit", textContent: "Verify" });
  btn.addEventListener("click", () => submit(d.key, inp.value));
  inp.addEventListener("keydown", e => { if (e.key === "Enter") submit(d.key, inp.value); });
  return el("div", { className: "text-captcha" }, [
    el("p", { className: "gc-instruction", textContent: "Type the characters you see" }),
    el("img", { id: "captcha-image", className: "captcha-image", alt: "captcha", src: d.image }),
    el("div", { className: "gc-buttons" }, [inp, btn])]);
}

function slideWidget(d, free) {
  const W = d.master_width, H = d.master_height;
  const tile = el("img", { className: "gc-tile", src: d.thumb, width: d.thumb_width, height: d.thumb_height });
  let x = d.display_x, y = d.display_y;
  const place = () => { tile.style.left = x + "px"; tile.style.top = y + "px"; };
  place();
  const body = el("div", { className: "gc-body", style: `width:${W}px;height:${H}px` }, [el("img", { className: "gc-master", src: d.master, width: W, height: H }), tile]);
  const kids = [el("p", { className: "gc-instruction", textContent: free ? "Drag the piece into the gap" : "Slide the piece into the gap" }), body];
  const clampX = v => Math.max(0, Math.min(W - d.thumb_width, v)), clampY = v => Math.max(0, Math.min(H - d.thumb_height, v));
  if (free) {
    dragger(tile, (dx, dy) => { x = clampX(d.display_x + dx); y = clampY(d.display_y + dy); place(); },
      () => submit(d.key, `${Math.round(x)},${Math.round(y)}`));
  } else {
    const handle = el("div", { className: "gc-handle" });
    kids.push(el("div", { className: "gc-track", style: `width:${W}px` }, [handle]));
    dragger(handle, dx => { const h = Math.max(0, Math.min(W - 40, dx)); handle.style.left = h + "px"; x = clampX(d.display_x + h); place(); },
      () => submit(d.key, `${Math.round(x)},${Math.round(y)}`));
  }
  return el("div", { className: free ? "gc-drag" : "gc-slide" }, kids);
}

function rotateWidget(d) {
  const S = d.master_width, T = d.thumb_size || d.thumb_width;
  const thumb = el("img", { className: "gc-thumb-rot", src: d.thumb, width: T, height: T, style: `left:${(S - T) / 2}px;top:${(S - T) / 2}px` });
  const body = el("div", { className: "gc-body", style: `width:${S}px;height:${S}px` }, [el("img", { className: "gc-master", src: d.master, width: S, height: S }), thumb]);
  const handle = el("div", { className: "gc-handle" });
  let angle = 0;
  dragger(handle, dx => { const h = Math.max(0, Math.min(S - 40, dx)); handle.style.left = h + "px"; angle = h / (S - 40) * 360; thumb.style.transform = `rotate(${angle}deg)`; },
    () => submit(d.key, Math.round(angle)));
  return el("div", { className: "gc-rotate" }, [el("p", { className: "gc-instruction", textContent: "Rotate the picture upright" }), body,
    el("div", { className: "gc-track", style: `width:${S}px` }, [handle])]);
}

function clickWidget(d) {
  const W = d.master_width, H = d.master_height;
  const pts = [];
  const master = el("img", { className: "gc-master", src: d.master, width: W, height: H });
  const body = el("div", { className: "gc-body", style: `width:${W}px;height:${H}px` }, [master]);
  body.addEventListener("click", e => {
    const r = body.getBoundingClientRect(); const x = Math.round(e.clientX - r.left), y = Math.round(e.clientY - r.top);
    pts.push(x, y);
    body.appendChild(el("div", { className: "gc-mark", textContent: String(pts.length / 2), style: `left:${x}px;top:${y}px` }));
  });
  const ok = el("button", { className: "gc-confirm", textContent: "Confirm" });
  ok.addEventListener("click", () => submit(d.key, pts.join(",")));
  const reset = el("button", { className: "gc-reset", textContent: "Reset" });
  reset.addEventListener("click", () => { pts.length = 0; body.querySelectorAll(".gc-mark").forEach(m => m.remove()); });
  return el("div", { className: "gc-click" }, [
    el("p", { className: "gc-instruction" }, [el("span", { textContent: "Click in this order:" }), el("img", { className: "gc-thumb", src: d.thumb, width: d.thumb_width, height: d.thumb_height })]),
    body, el("div", { className: "gc-buttons" }, [reset, ok])]);
}

async function load() {
  document.body.dataset.state = "loading";
  document.body.dataset.verdict = "";
  const d = await (await fetch("/api/new?t=" + encodeURIComponent(type))).json();
  box.replaceChildren(type === "text" ? textWidget(d) : type === "go-slide" ? slideWidget(d, false) : type === "go-drag" ? slideWidget(d, true)
    : type === "go-rotate" ? rotateWidget(d) : clickWidget(d));
  document.body.dataset.round = String(Number(document.body.dataset.round) + 1);
  v.textContent = "waiting for an answer"; v.className = "verdict";
  await Promise.all([...box.querySelectorAll("img")].map(i => i.decode().catch(() => {})));
  document.body.dataset.state = "ready";
}
load();
