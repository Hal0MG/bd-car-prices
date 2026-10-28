"use client";

import { useEffect, useRef, useState } from "react";
import { inWords, plain, taka, takaShort } from "@/lib/format";
import { t } from "@/lib/i18n/en";
import { INTRO_SEEN_KEY, LAST_STOP, type Split, type Story } from "@/lib/intro";
import { DhakaPlate, JapanPlate } from "./Plates";
import type { Globe } from "./globe";

// Corners of the plate frame in /intro/prado-front.jpg, as fractions of its width and height:
// top left, top right, bottom right, bottom left. Measured from the photo.
const PLATE_CORNERS: [number, number][] = [[0.1858, 0.5671], [0.3326, 0.6167], [0.3333, 0.7431], [0.1875, 0.6898]];
const PLATE_W = 200, PLATE_H = 100;

/** The projective transform that takes a w×h rectangle onto four points, as a CSS matrix3d. */
function warp(w: number, h: number, pts: [number, number][]) {
  const src = [[0, 0], [w, 0], [w, h], [0, h]], A: number[][] = [], b: number[] = [];
  src.forEach(([x, y], i) => {
    const [u, v] = pts[i];
    A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.push(u);
    A.push([0, 0, 0, x, y, 1, -v * x, -v * y]); b.push(v);
  });
  for (let c = 0; c < 8; c++) {   // Gaussian elimination with partial pivoting
    let p = c;
    for (let r = c + 1; r < 8; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
    [A[c], A[p]] = [A[p], A[c]]; [b[c], b[p]] = [b[p], b[c]];
    for (let r = 0; r < 8; r++) if (r !== c) {
      const k = A[r][c] / A[c][c];
      for (let j = c; j < 8; j++) A[r][j] -= k * A[c][j];
      b[r] -= k * b[c];
    }
  }
  const [a, bb, c, d, e, f, g, hh] = b.map((v, i) => v / A[i][i]);
  return `matrix3d(${a},${d},0,${g},${bb},${e},0,${hh},0,0,1,0,${c},${f},0,1)`;
}

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const ease = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
/** Story position for a stop: 0 is the opening; stop k shows at k + 0.62, once its camera move, route and lines have played. */
const at = (k: number) => (k === 0 ? 0 : k + 0.62);

/**
 * "Two plates": the first-visit intro. The same Prado wears a Japanese plate and a Dhaka one, then a
 * button walks it from Yokohama to Dhaka while the slip fills in. Shown once per browser over the
 * home page; the footer's replay link brings it back.
 */
export function TwoPlates({ story }: { story: Story }) {
  const rootRef = useRef<HTMLDivElement>(null);
  const goRef = useRef<(k: number) => void>(() => {});
  const closeRef = useRef<() => void>(() => {});
  const [step, setStep] = useState(0);

  useEffect(() => {
    const root = rootRef.current!;
    const html = document.documentElement;
    if (html.dataset.intro !== "show") return;
    const $ = <T extends HTMLElement>(sel: string) => root.querySelector(sel) as T;
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const phone = () => root.clientWidth <= 860;

    const opening = $(".opening"), panel = $(".panel"), globeBox = $(".globe-box"), lwin = $(".lwin"), rowsEl = $(".lines");
    const totalEl = $(".total"), wordsEl = $(".total-words"), leadEl = $(".share-lead"), captionEl = $(".caption");
    const jpSlip = $(".carslot .jp-wrap"), bdSlip = $(".carslot .bd-wrap");
    const bar = { car: $(".share-car"), tax: $(".share-tax"), fees: $(".share-fees") } as Record<Split, HTMLElement>;
    const lineEls = [...root.querySelectorAll<HTMLElement>(".line")];
    const frames = [...root.querySelectorAll<HTMLElement>(".frame")];

    function fitPlates() {
      for (const fr of frames) {
        const pts = PLATE_CORNERS.map(([x, y]) => [x * fr.clientWidth, y * fr.clientHeight] as [number, number]);
        fr.querySelector<HTMLElement>(".plate")!.style.transform = warp(PLATE_W, PLATE_H, pts);
      }
    }
    // the slip is a fixed size from the start, so nothing on it moves as it fills in
    function sizeLedger() {
      const room = root.clientHeight - 32 - (phone() ? root.clientHeight * 0.4 : 0);
      lwin.style.height = "auto";
      const others = panel.firstElementChild!.clientHeight - lwin.offsetHeight;
      lwin.style.height = `${Math.max(80, Math.min(rowsEl.scrollHeight, room - others))}px`;
    }

    let lastStop = -1, lastTotal = -1, captionTimer = 0;
    function updateSlip(s: number) {
      const stop = Math.min(LAST_STOP, Math.floor(s));
      const sum: Record<Split, number> = { car: 0, tax: 0, fees: 0 };
      let lastOn: HTMLElement | null = null;
      story.lines.forEach((l, i) => {
        const on = s >= l.stop + 0.12, el = lineEls[i];
        el.classList.toggle("on", on);
        el.classList.toggle("now", on && l.stop === stop && stop < LAST_STOP);
        if (on) lastOn = el;
        if (on && l.split) sum[l.split] += l.amount;
      });
      // keep the newest line in view; only moves when the window is shorter than the list
      const winH = lwin.clientHeight, bottom = lastOn ? (lastOn as HTMLElement).offsetTop + (lastOn as HTMLElement).offsetHeight : 0;
      rowsEl.style.transform = `translateY(${-Math.max(0, bottom - winH)}px)`;
      lwin.classList.toggle("scrolled", bottom > winH);
      const total = sum.car + sum.tax + sum.fees;
      if (total !== lastTotal) {
        lastTotal = total;
        totalEl.textContent = taka(total);
        wordsEl.textContent = inWords(total);
        for (const k of ["car", "tax", "fees"] as Split[]) bar[k].style.flexGrow = String(sum[k]);
        leadEl.innerHTML = sum.tax ? `<b>${Math.round(sum.tax / total * 100)}%</b> ${t.slip.shareLead}` : "";
      }
      if (stop !== lastStop) {
        lastStop = stop;
        captionEl.classList.add("out");
        clearTimeout(captionTimer);
        captionTimer = window.setTimeout(() => { captionEl.innerHTML = story.captions[lastStop]; captionEl.classList.remove("out"); }, reduced ? 0 : 200);
      }
    }
    function updateStage(s: number) {
      const h = ease(clamp01((s - 0.45) / 0.5));   // the opening hands over to the globe and slip
      opening.style.opacity = String(1 - Math.min(1, h * 2.2));
      opening.style.visibility = h >= 0.5 ? "hidden" : "visible";
      panel.style.opacity = String(clamp01((h - 0.55) / 0.4));
      panel.style.visibility = h > 0.55 ? "visible" : "hidden";
      globeBox.style.opacity = String(clamp01((h - 0.4) / 0.5));
      // registered at BRTA: the Japanese plate comes off, the Dhaka one goes on
      const dhaka = s >= LAST_STOP - 0.85;
      bdSlip.style.opacity = dhaka ? "1" : "0"; jpSlip.style.opacity = dhaka ? "0" : "1";
      updateSlip(s);
    }

    // buttons drive the story: each press plays one stop
    let sCur = 0, from = 0, to = 0, t0 = 0, dur = 0, cur = 0;
    goRef.current = (k: number) => {
      cur = Math.max(0, Math.min(LAST_STOP, k));
      from = sCur; to = at(cur); t0 = performance.now();
      dur = reduced ? 0 : Math.min(2600, 1400 * Math.abs(to - from));
      setStep(cur);
    };
    let globe: Globe | null = null, raf = 0, last = performance.now(), sDrawn = -1, alive = true;
    const frame = (now: number) => {
      raf = requestAnimationFrame(frame);
      const dt = Math.min(0.1, (now - last) / 1000); last = now;
      sCur = dur ? from + (to - from) * Math.min(1, (now - t0) / dur) : to;
      if (sCur !== sDrawn) { sDrawn = sCur; updateStage(sCur); }
      globe?.frame(sCur, dt);
    };
    const resize = () => { fitPlates(); sizeLedger(); globe?.resize(); updateStage(sCur); };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") goRef.current(cur + 1);
      else if (e.key === "ArrowLeft" && cur > 1) goRef.current(cur - 1);
      else if (e.key === "Escape") closeRef.current();
    };
    addEventListener("resize", resize);
    addEventListener("keydown", onKey);
    document.fonts?.ready.then(() => alive && resize());
    resize();
    raf = requestAnimationFrame(frame);

    // the globe and its map data are a separate download, fetched only now the intro is showing
    let webgl = false;
    try { webgl = !!document.createElement("canvas").getContext("webgl2"); } catch {}
    if (webgl) {
      import("./globe").then(({ startGlobe }) => {
        if (!alive) return;
        globe = startGlobe(root.querySelector("canvas")!, $(".pins"), { phone, reduced });
        globe.resize();
      }).catch(() => {});   // without the globe, the slip still tells the story
    }

    closeRef.current = () => {
      try { localStorage.setItem(INTRO_SEEN_KEY, "seen"); } catch {}
      delete html.dataset.intro;
      if (location.search.includes("intro")) history.replaceState(null, "", location.pathname);
      cleanup();
    };
    function cleanup() {
      alive = false;
      cancelAnimationFrame(raf);
      clearTimeout(captionTimer);
      removeEventListener("resize", resize);
      removeEventListener("keydown", onKey);
      globe?.dispose(); globe = null;
    }
    return cleanup;
  }, [story]);

  const close = (focusCalculator?: boolean) => {
    closeRef.current();
    if (focusCalculator) document.querySelector<HTMLElement>(".calc-form button, .calc-form input, .calc-form select")?.focus();
  };
  const T = t.intro;

  return (
    <div className="intro-layer" ref={rootRef} role="dialog" aria-modal="true" aria-label={T.title}>
      <button type="button" className="intro-skip" onClick={() => close()}>{T.skip}</button>
      <div className="globe-box"><canvas aria-hidden="true" /><div className="pins" aria-hidden="true" /></div>

      <section className="opening">
        <h1>{T.title}</h1>
        <p className="sub">{T.sub(takaShort(story.dhaka - story.japan))}</p>
        <div className="pair">
          <figure className="shot">
            <div className="print"><div className="frame">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/intro/prado-front.jpg" alt={T.altJapan} width={800} height={600} />
              <JapanPlate />
            </div></div>
            <figcaption><span className="eyebrow">{T.japanPlate}</span><b>{takaShort(story.japan)}</b></figcaption>
          </figure>
          <figure className="shot">
            <div className="print"><div className="frame">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/intro/prado-front.jpg" alt={T.altDhaka} width={800} height={600} />
              <DhakaPlate />
            </div></div>
            <figcaption><span className="eyebrow">{T.dhakaPlate}</span><b className="dhaka">{takaShort(story.dhaka)}</b></figcaption>
          </figure>
        </div>
        <button type="button" className="btn" onClick={() => goRef.current(1)}>{T.start}</button>
      </section>

      <aside className="panel">
        <section className="slip" aria-label={t.slip.heading}>
          <div className="carslot">
            <div className="jp-wrap"><JapanPlate /></div>
            <div className="bd-wrap" style={{ opacity: 0 }}><DhakaPlate /></div>
          </div>
          <p className="eyebrow">{t.slip.heading}</p>
          <p className="total num" />
          <p className="total-words" />
          <p className="share-lead" />
          <div className="share-bar" aria-hidden="true"><span className="share-car" /><span className="share-tax" /><span className="share-fees" /></div>
          <p className="caption" aria-live="polite" />
          <div className="lwin">
            <div className="lines num">
              {story.lines.map((l, i) => (
                <div key={i} className={`line ${l.kind ?? ""}`}><span>{l.label}</span><span className="r">{plain(l.amount)}</span></div>
              ))}
            </div>
          </div>
          <div className="intro-steps">
            <button type="button" className="btn ghost" aria-label={T.back} disabled={step <= 1} onClick={() => goRef.current(step - 1)}>←</button>
            {step < LAST_STOP
              ? <button type="button" className="btn" onClick={() => goRef.current(step + 1)}>{T.next}</button>
              : <button type="button" className="btn" onClick={() => close(true)}>{T.done}</button>}
            {step > 0 && <span className="eyebrow count">{step} / {LAST_STOP}</span>}
          </div>
        </section>
      </aside>
    </div>
  );
}
