// The intro's globe: an old brown map in the site's own inks, painted from Natural Earth
// coastlines (public domain) and lit as a 3D object. Loaded on demand, only when the intro shows.
import * as THREE from "three";
import { feature } from "topojson-client";
import type { GeometryObject, Topology } from "topojson-specification";
import landTopo from "world-atlas/land-50m.json";
import countryTopo from "world-atlas/countries-50m.json";
import { LAST_STOP } from "@/lib/intro";

type Geom = { type: string; coordinates: unknown };
type Features = { features: { geometry: Geom; properties: { name?: string } }[] };

export interface Globe {
  /** draw the globe for story position `s`; `dt` is seconds since the last frame */
  frame(s: number, dt: number): void;
  resize(): void;
  dispose(): void;
}

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const ease = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const wrap = (a: number) => ((a + 540) % 360) - 180;

// Yokohama, round Singapore, into Chattogram; then the road to Dhaka
const SEA: [number, number][] = [[35.44, 139.64], [34.6, 139.9], [33.0, 136.0], [31.0, 131.5], [28.0, 127.0], [24.5, 122.6], [20.6, 120.4], [14.0, 114.0],
  [8.0, 108.5], [3.0, 105.5], [1.25, 104.0], [2.6, 101.2], [5.6, 98.0], [6.6, 94.0], [13.0, 91.2], [19.5, 91.0], [22.27, 91.8]];
const ROAD: [number, number][] = [[22.33, 91.83], [23.0, 91.4], [23.46, 91.18], [23.81, 90.41]];
const PLACES: [string, number, number, number][] = [["Yokohama", 35.44, 139.64, 0], ["Chattogram", 22.33, 91.83, 16], ["Dhaka", 23.81, 90.41, -16]];

// Camera stops, one per stop on the slip: the globe turns about its axis and the camera rises to the
// latitude. `d` is distance from the centre in globe radii. Stop 2 follows the ship instead.
type View = { lat: number; lon: number; d: number };
const STOPS: (View | null)[] = [
  { lat: 30, lon: 125, d: 3.2 }, { lat: 34, lon: 136, d: 2.2 }, null,
  { lat: 22.6, lon: 91.4, d: 1.75 }, { lat: 23.6, lon: 90.4, d: 1.7 }, { lat: 23.6, lon: 90.4, d: 1.7 }, { lat: 23.4, lon: 90.8, d: 1.6 },
  { lat: 22, lon: 112, d: 3.2 },
];
// the sea route draws once the camera reaches Japan's coast, finishing before stop 2 settles
const seaP = (s: number) => clamp01((s - 2.05) / 0.5);
const roadP = (s: number) => clamp01((s - 6.05) / 0.5);
// the sharp detail layer covers this window, so Bangladesh stays crisp up close
const ASIA = { lon0: 60, lon1: 150, lat0: 50, lat1: -10 };

export function startGlobe(canvas: HTMLCanvasElement, pinsEl: HTMLElement, opts: { phone: () => boolean; reduced: boolean }): Globe {
  const css = getComputedStyle(document.documentElement);
  const tok = (n: string) => css.getPropertyValue(n).trim();
  const land = feature(landTopo as unknown as Topology, (landTopo as unknown as Topology).objects.land as GeometryObject) as unknown as Features;
  const countries = feature(countryTopo as unknown as Topology, (countryTopo as unknown as Topology).objects.countries as GeometryObject) as unknown as Features;

  // paint() draws the map for a lon/lat window. It runs twice: the whole globe, and Asia at four times the detail.
  function paint(W: number, H: number, lon0: number, lon1: number, lat0: number, lat1: number) {
    const cv = document.createElement("canvas"); cv.width = W; cv.height = H;
    const g = cv.getContext("2d")!;
    const X = (lon: number) => (lon - lon0) / (lon1 - lon0) * W, Y = (lat: number) => (lat0 - lat) / (lat0 - lat1) * H;
    const k = W / (lon1 - lon0) / (4096 / 360);   // line widths scale with detail, so both layers match
    const trace = (geom: Geom) => {
      g.beginPath();
      const polys = (geom.type === "Polygon" ? [geom.coordinates] : geom.type === "MultiPolygon" ? geom.coordinates : []) as [number, number][][][];
      for (const poly of polys) for (const ring of poly) ring.forEach(([lo, la], i) => (i ? g.lineTo(X(lo), Y(la)) : g.moveTo(X(lo), Y(la))));
    };
    const sea = g.createLinearGradient(0, Y(90), 0, Y(-90));
    sea.addColorStop(0, "#6e5536"); sea.addColorStop(0.3, "#9a7b52"); sea.addColorStop(0.5, "#a6875c"); sea.addColorStop(0.7, "#9a7b52"); sea.addColorStop(1, "#6e5536");
    g.fillStyle = sea; g.fillRect(0, 0, W, H);
    g.lineJoin = "round";
    for (const [w, a] of [[30, 0.05], [18, 0.07], [9, 0.1]]) {   // engraved water lines along the coast
      g.strokeStyle = `rgba(29,27,22,${a})`; g.lineWidth = w * k;
      for (const f of land.features) { trace(f.geometry); g.stroke(); }
    }
    g.fillStyle = tok("--globe-land");
    for (const f of land.features) { trace(f.geometry); g.fill("evenodd"); }
    for (const f of countries.features) if (f.properties.name === "Bangladesh") {
      g.fillStyle = tok("--globe-home"); trace(f.geometry); g.fill("evenodd");
      g.strokeStyle = "#8a3b1e"; g.lineWidth = 3 * k; g.stroke();
    }
    g.strokeStyle = "rgba(29,27,22,.28)"; g.lineWidth = 1.1 * k;
    for (const f of countries.features) { trace(f.geometry); g.stroke(); }
    g.strokeStyle = "#1d1b16"; g.lineWidth = 2 * k;
    for (const f of land.features) { trace(f.geometry); g.stroke(); }
    g.strokeStyle = "rgba(29,27,22,.22)"; g.lineWidth = 1.2 * k;
    for (let lo = -180; lo <= 180; lo += 15) { g.beginPath(); g.moveTo(X(lo), 0); g.lineTo(X(lo), H); g.stroke(); }
    for (let la = -75; la <= 75; la += 15) { g.beginPath(); g.moveTo(0, Y(la)); g.lineTo(W, Y(la)); g.stroke(); }
    return cv;
  }

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.05, 50);
  scene.add(camera);
  const key = new THREE.DirectionalLight(0xfff3e0, 2.1); key.position.set(-2.2, 1.8, 1.8); camera.add(key);
  scene.add(new THREE.HemisphereLight(0xfffaf0, 0x6b5a44, 0.75));
  const texture = (cv: HTMLCanvasElement) => {
    const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = renderer.capabilities.getMaxAnisotropy(); return t;
  };
  const globe = new THREE.Group(); scene.add(globe);
  globe.add(new THREE.Mesh(new THREE.SphereGeometry(1, 128, 96), new THREE.MeshStandardMaterial({ map: texture(paint(4096, 2048, -180, 180, 90, -90)), roughness: 0.85 })));
  const rad = Math.PI / 180, a = ASIA;
  const aw = opts.phone() ? 2048 : 4096;
  const patch = new THREE.SphereGeometry(1.0006, 96, 64, (a.lon0 + 180) * rad, (a.lon1 - a.lon0) * rad, (90 - a.lat0) * rad, (a.lat0 - a.lat1) * rad);
  globe.add(new THREE.Mesh(patch, new THREE.MeshStandardMaterial({ map: texture(paint(aw, Math.round(aw * (a.lat0 - a.lat1) / (a.lon1 - a.lon0)), a.lon0, a.lon1, a.lat0, a.lat1)), roughness: 0.85 })));

  // lat/lon on the sphere, matching SphereGeometry's texture layout
  const P = (lat: number, lon: number, r = 1) => {
    const phi = (90 - lat) * rad, th = (lon + 180) * rad;
    return new THREE.Vector3(-r * Math.sin(phi) * Math.cos(th), r * Math.cos(phi), r * Math.sin(phi) * Math.sin(th));
  };
  // great-circle steps between waypoints, so the line hugs the curve of the globe
  function arc(pts: [number, number][], r: number, per = 24) {
    const out: THREE.Vector3[] = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const p = P(...pts[i]).normalize(), q = P(...pts[i + 1]).normalize(), ang = p.angleTo(q), s = Math.sin(ang) || 1;
      for (let j = 0; j < per; j++) { const t = j / per; out.push(p.clone().multiplyScalar(Math.sin((1 - t) * ang) / s).add(q.clone().multiplyScalar(Math.sin(t * ang) / s)).multiplyScalar(r)); }
    }
    out.push(P(...pts[pts.length - 1], r));
    return new THREE.CatmullRomCurve3(out);
  }
  const rust = new THREE.Color("#8a3b1e");
  function routeLine(curve: THREE.CatmullRomCurve3, segs: number) {
    const geo = new THREE.TubeGeometry(curve, segs, 0.0015, 6, false);
    globe.add(new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: rust })));
    return (p: number) => geo.setDrawRange(0, Math.floor(segs * p) * 36);
  }
  const seaCurve = arc(SEA, 1.003), roadCurve = arc(ROAD, 1.003, 10);
  const drawSea = routeLine(seaCurve, 900), drawRoad = routeLine(roadCurve, 120);
  const ship = new THREE.Mesh(new THREE.SphereGeometry(0.008, 20, 16), new THREE.MeshBasicMaterial({ color: 0x1d1b16 }));
  globe.add(ship);
  const pins = PLACES.map(([name, lat, lon, dy]) => {
    const el = document.createElement("div"); el.className = "pin"; el.textContent = name; pinsEl.appendChild(el);
    return { el, p: P(lat, lon, 1.002), dy };
  });

  const toLatLon = (v: THREE.Vector3) => { const n = v.clone().normalize(); return { lat: 90 - Math.acos(n.y) / rad, lon: Math.atan2(n.z, -n.x) / rad - 180 }; };
  const stopView = (i: number, s: number): View => STOPS[i] ?? { ...toLatLon(seaCurve.getPointAt(seaP(s))), d: 2.8 };
  function view(s: number): View {
    const i = Math.floor(s), from = stopView(i, s);
    if (i >= LAST_STOP) return from;
    const to = stopView(i + 1, s), t = ease(clamp01((s - i - 0.72) / 0.28));   // move in the last stretch of each stop
    return { lat: lerp(from.lat, to.lat, t), lon: from.lon + wrap(to.lon - from.lon) * t, d: lerp(from.d, to.d, t) };
  }

  let W = 1, H = 1, dirty = true, sPrev = -1;
  const cur = view(0);
  const v3 = new THREE.Vector3(), camDir = new THREE.Vector3();
  return {
    resize() {
      W = canvas.clientWidth; H = canvas.clientHeight;
      renderer.setSize(W, H, false); camera.aspect = W / H; camera.updateProjectionMatrix();
      dirty = true;
    },
    frame(s, dt) {
      const want = view(s);
      let moving = false;
      if (opts.reduced) Object.assign(cur, want);
      else {
        const k = 1 - Math.exp(-dt * 6), dl = wrap(want.lon - cur.lon);
        moving = Math.abs(dl) + Math.abs(want.lat - cur.lat) + Math.abs(want.d - cur.d) > 0.002;
        cur.lon += dl * k; cur.lat += (want.lat - cur.lat) * k; cur.d += (want.d - cur.d) * k;
      }
      if (!dirty && !moving && s === sPrev) return;
      dirty = false; sPrev = s;
      const p = P(0, cur.lon); globe.rotation.y = Math.atan2(-p.x, p.z);
      const la = cur.lat * rad, d = 1 + (cur.d - 1) * (opts.phone() ? 1.25 : 1);   // narrow screens stand back a little
      camera.position.set(0, Math.sin(la) * d, Math.cos(la) * d); camera.lookAt(0, 0, 0);
      const sp = seaP(s);
      drawSea(sp); drawRoad(roadP(s));
      ship.position.copy(seaCurve.getPointAt(sp)); ship.visible = s >= 1.8 && s < 3.4;
      renderer.render(scene, camera);
      camera.getWorldDirection(camDir).negate();
      for (const pin of pins) {
        v3.copy(pin.p).applyMatrix4(globe.matrixWorld);
        const facing = v3.clone().normalize().dot(camDir);
        v3.project(camera);
        pin.el.style.opacity = facing > 0.25 ? "1" : "0";
        pin.el.style.transform = `translate(${((v3.x + 1) / 2 * W + 10).toFixed(1)}px, ${((1 - v3.y) / 2 * H + pin.dy).toFixed(1)}px) translateY(-50%)`;
      }
    },
    dispose() {
      scene.traverse((o) => {
        if (o instanceof THREE.Mesh) { o.geometry.dispose(); const m = o.material as THREE.MeshStandardMaterial; m.map?.dispose(); m.dispose(); }
      });
      renderer.dispose();
      pinsEl.replaceChildren();
    },
  };
}
