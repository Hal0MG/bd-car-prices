/**
 * The site's sounds, all made in the browser with Web Audio: no files to download or license.
 * Browsers only allow sound after the visitor clicks or presses a key, so nothing plays before that.
 * The choice to mute is kept in localStorage.
 */

/** localStorage key; "off" means muted. */
export const SOUND_KEY = "sd-sound";
/** fired on window when sound is switched on or off */
export const SOUND_EVENT = "sd-sound";

const VOLUME = 0.8;
let ctx: AudioContext | null = null, master: GainNode, noiseBuf: AudioBuffer;
let drone: { stop: (fade: number) => void } | null = null;

export function soundOn() {
  try { return localStorage.getItem(SOUND_KEY) !== "off"; } catch { return true; }
}

export function setSound(on: boolean) {
  try { localStorage.setItem(SOUND_KEY, on ? "on" : "off"); } catch {}
  if (ctx) master.gain.setTargetAtTime(on ? VOLUME : 0, ctx.currentTime, 0.05);
  dispatchEvent(new Event(SOUND_EVENT));
}

/** The audio graph, made on first use. Call from a click or key handler so the browser lets it start. */
function audio() {
  if (!ctx) {
    const AC = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AC) return null;
    ctx = new AC();
    const comp = ctx.createDynamicsCompressor();
    comp.connect(ctx.destination);
    master = ctx.createGain();
    master.gain.value = soundOn() ? VOLUME : 0;
    master.connect(comp);
    noiseBuf = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
    const d = noiseBuf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  }
  if (ctx.state === "suspended") ctx.resume();
  return ctx;
}

/** a gain node into the master bus with a quick attack and exponential decay */
function env(c: AudioContext, t: number, peak: number, attack: number, decay: number) {
  const g = c.createGain();
  g.gain.setValueAtTime(0.0001, t);
  g.gain.exponentialRampToValueAtTime(peak, t + attack);
  g.gain.exponentialRampToValueAtTime(0.0001, t + attack + decay);
  g.connect(master);
  return g;
}

function tone(c: AudioContext, t: number, type: OscillatorType, f0: number, f1: number, out: AudioNode, len: number) {
  const o = c.createOscillator();
  o.type = type;
  o.frequency.setValueAtTime(f0, t);
  if (f1 !== f0) o.frequency.exponentialRampToValueAtTime(f1, t + len);
  o.connect(out); o.start(t); o.stop(t + len + 0.05);
}

function noise(c: AudioContext, t: number, len: number, out: AudioNode) {
  const s = c.createBufferSource();
  s.buffer = noiseBuf; s.loop = true;
  s.connect(out); s.start(t); s.stop(t + len);
  return s;
}

/** a soft tick for buttons and links */
export function click() {
  const c = audio(); if (!c) return;
  const t = c.currentTime;
  tone(c, t, "sine", 2400, 1400, env(c, t, 0.05, 0.002, 0.04), 0.05);
  const bp = c.createBiquadFilter();
  bp.type = "bandpass"; bp.frequency.value = 4000; bp.Q.value = 2;
  bp.connect(env(c, t, 0.04, 0.001, 0.012));
  noise(c, t, 0.02, bp);
}

// A minor pentatonic, so ledger lines climb without ever clashing with the drone.
const SCALE = [0, 3, 5, 7, 10, 12, 15, 17, 19, 22, 24, 27];
const note = (semis: number) => 440 * Math.pow(2, semis / 12);

/** a line arriving on the slip; i is its place in the list, so the slip climbs as it fills */
export function blip(i: number, delay = 0) {
  const c = audio(); if (!c) return;
  const t = c.currentTime + delay, f = note(SCALE[i % SCALE.length]);
  tone(c, t, "triangle", f, f, env(c, t, 0.09, 0.004, 0.35), 0.4);
  tone(c, t, "sine", f * 2, f * 2, env(c, t, 0.03, 0.002, 0.15), 0.2);
}

/** a heavy line, like supplementary duty: a low hit under the blip */
export function thud(delay = 0) {
  const c = audio(); if (!c) return;
  const t = c.currentTime + delay;
  tone(c, t, "sine", 110, 40, env(c, t, 0.35, 0.005, 0.5), 0.55);
  const lp = c.createBiquadFilter();
  lp.type = "lowpass"; lp.frequency.value = 600;
  lp.connect(env(c, t, 0.12, 0.002, 0.08));
  noise(c, t, 0.1, lp);
}

/** the plate swap at BRTA: a metal clack */
export function clack() {
  const c = audio(); if (!c) return;
  const t = c.currentTime;
  for (const [dt, f] of [[0, 1800], [0.07, 1300]]) {
    const bp = c.createBiquadFilter();
    bp.type = "bandpass"; bp.frequency.value = f; bp.Q.value = 8;
    bp.connect(env(c, t + dt, 0.5, 0.001, 0.09));
    noise(c, t + dt, 0.1, bp);
    tone(c, t + dt, "square", f / 4, f / 5, env(c, t + dt, 0.03, 0.001, 0.06), 0.08);
  }
}

/** the camera moving between stops: filtered noise swept up and back down */
export function whoosh(len: number) {
  const c = audio(); if (!c) return;
  len = Math.max(0.4, len);
  const t = c.currentTime;
  const bp = c.createBiquadFilter();
  bp.type = "bandpass"; bp.Q.value = 1.2;
  bp.frequency.setValueAtTime(250, t);
  bp.frequency.exponentialRampToValueAtTime(1600, t + len * 0.45);
  bp.frequency.exponentialRampToValueAtTime(300, t + len);
  const g = c.createGain();
  g.gain.setValueAtTime(0.0001, t);
  g.gain.exponentialRampToValueAtTime(0.09, t + len * 0.45);
  g.gain.exponentialRampToValueAtTime(0.0001, t + len);
  bp.connect(g); g.connect(master);
  noise(c, t, len + 0.05, bp);
}

/** the last stop: a chord that settles */
export function arrive(delay = 0) {
  const c = audio(); if (!c) return;
  const t = c.currentTime + delay;
  for (const [i, s] of [-12, 0, 7, 12, 15].entries()) {
    const f = note(s);
    tone(c, t + i * 0.06, "triangle", f, f, env(c, t + i * 0.06, 0.06, 0.08, 2.6), 2.8);
  }
}

/** a low, slowly moving pad under the intro; starting it twice does nothing */
export function startDrone() {
  const c = audio(); if (!c || drone) return;
  const t = c.currentTime;
  const out = c.createGain();
  out.gain.setValueAtTime(0.0001, t);
  out.gain.exponentialRampToValueAtTime(0.07, t + 2.5);
  out.connect(master);
  const lp = c.createBiquadFilter();
  lp.type = "lowpass"; lp.frequency.value = 420; lp.Q.value = 3;
  lp.connect(out);
  const lfo = c.createOscillator(), depth = c.createGain();
  lfo.frequency.value = 0.07; depth.gain.value = 220;
  lfo.connect(depth); depth.connect(lp.frequency);
  const oscs = [lfo];
  for (const [f, type] of [[55, "sawtooth"], [55.4, "sawtooth"], [82.4, "sawtooth"], [27.5, "sine"]] as const) {
    const o = c.createOscillator();
    o.type = type; o.frequency.value = f;
    o.connect(lp); oscs.push(o);
  }
  oscs.forEach((o) => o.start(t));
  drone = {
    stop(fade) {
      const now = c.currentTime;
      out.gain.cancelScheduledValues(now);
      out.gain.setTargetAtTime(0.0001, now, fade / 4);
      oscs.forEach((o) => o.stop(now + fade));
    },
  };
}

export function stopDrone(fade = 1.2) {
  drone?.stop(fade);
  drone = null;
}

let clicksOn = false;
/** a tick for every button, link and menu on the page; installing it twice does nothing */
export function installClickSounds() {
  if (clicksOn) return;
  clicksOn = true;
  document.addEventListener("click", (e) => {
    const el = (e.target as Element | null)?.closest?.("button, a[href], summary, [role=button], input[type=checkbox], input[type=radio]");
    if (el && !(el as HTMLButtonElement).disabled) click();
  }, true);
  document.addEventListener("change", (e) => {
    if ((e.target as Element).matches?.("select")) click();
  }, true);
}
