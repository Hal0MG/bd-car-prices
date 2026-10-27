import type { Segment } from "@/lib/market";

// Side-profile outlines drawn on a 320×150 grid. The ground line is y=112;
// each shape lists where its two wheels sit.
interface Shape {
  body: string;
  glass: string;
  lines: string;
  wheels: [number, number];
  /** cars face left; x of the headlamp and the door mirror */
  lamp: number;
  mirror: [number, number];
}

const SHAPES: Record<Segment, Shape> = {
  sedan: {
    body: "M24 112 L24 98 Q26 88 42 86 L96 80 L130 56 Q138 50 154 49 L206 49 Q220 50 230 58 L258 80 L292 84 Q302 86 302 98 L302 112 Z",
    glass: "M106 80 L134 59 Q140 54 154 54 L176 54 L176 80 Z M182 80 L182 54 L204 54 Q216 55 226 62 L248 80 Z",
    lines: "M60 96 L282 96 M178 84 L178 108 M120 90 L132 90 M196 90 L208 90",
    wheels: [72, 252], lamp: 32, mirror: [100, 80],
  },
  hatchback: {
    body: "M34 112 L34 98 Q36 88 52 86 L96 80 L126 54 Q134 47 150 47 L222 47 Q238 48 248 62 L268 90 Q276 94 276 104 L276 112 Z",
    glass: "M106 80 L130 58 Q136 52 150 52 L170 52 L170 80 Z M176 80 L176 52 L220 52 Q232 53 240 64 L250 80 Z",
    lines: "M64 96 L262 96 M173 84 L173 108 M118 90 L130 90 M190 90 L202 90",
    wheels: [78, 234], lamp: 42, mirror: [100, 80],
  },
  wagon: {
    body: "M24 112 L24 98 Q26 88 42 86 L96 80 L128 52 Q136 46 152 46 L278 46 Q290 47 294 58 L300 86 Q302 90 302 98 L302 112 Z",
    glass: "M106 80 L132 56 Q138 51 152 51 L176 51 L176 80 Z M182 80 L182 51 L232 51 L232 80 Z M238 80 L238 51 L276 51 Q284 52 287 60 L292 80 Z",
    lines: "M60 96 L290 96 M179 84 L179 108 M235 84 L235 108 M120 90 L132 90 M196 90 L208 90",
    wheels: [72, 256], lamp: 32, mirror: [100, 80],
  },
  suv: {
    body: "M20 112 L20 86 Q22 74 38 72 L78 68 L106 36 Q112 30 124 30 L254 30 Q268 30 276 42 L292 66 Q304 70 304 84 L304 112 Z",
    glass: "M88 68 L112 38 Q116 35 124 35 L172 35 L172 68 Z M178 68 L178 35 L236 35 L236 68 Z M242 68 L242 35 L254 35 Q264 35 270 44 L285 68 Z",
    lines: "M44 92 L292 92 M175 72 L175 108 M239 72 L239 108 M112 82 L124 82 M192 82 L204 82",
    wheels: [72, 254], lamp: 28, mirror: [84, 68],
  },
  minivan: {
    body: "M18 112 L18 90 Q20 78 34 76 L58 72 L84 30 Q88 24 100 24 L280 24 Q296 24 298 40 L302 96 L302 112 Z",
    glass: "M66 72 L88 34 Q91 30 100 30 L132 30 L132 72 Z M138 72 L138 30 L204 30 L204 72 Z M210 72 L210 30 L278 30 Q290 30 291 42 L293 72 Z",
    lines: "M40 92 L296 92 M135 76 L135 108 M207 76 L207 108 M150 84 L200 84 M118 84 L128 84",
    wheels: [66, 260], lamp: 26, mirror: [64, 72],
  },
  coupe: {
    body: "M18 112 L20 100 Q24 90 50 86 L118 78 L156 56 Q170 50 190 50 L214 51 Q236 54 256 72 L294 82 Q304 86 304 98 L304 112 Z",
    glass: "M128 78 L160 59 Q170 55 186 55 L196 55 L196 78 Z M202 78 L202 56 L212 56 Q230 58 244 72 L246 78 Z",
    lines: "M56 100 L286 100 M199 82 L199 108 M216 92 L228 92",
    wheels: [70, 252], lamp: 28, mirror: [124, 78],
  },
  convertible: {
    body: "M20 112 L22 100 Q26 90 50 86 L126 80 L238 80 L292 84 Q304 88 304 100 L304 112 Z",
    glass: "",
    lines: "M126 80 L146 56 L152 57 L138 80 M180 80 Q182 66 194 64 Q202 64 204 72 M210 80 Q212 66 224 64 Q232 64 234 72 M56 100 L286 100 M170 84 L170 108",
    wheels: [72, 254], lamp: 30, mirror: [132, 80],
  },
};

export const SEGMENT_LABEL: Record<Segment, string> = {
  sedan: "Sedan", hatchback: "Hatchback", wagon: "Wagon", suv: "SUV",
  minivan: "Microbus", coupe: "Coupe", convertible: "Convertible",
};

interface Props {
  segment: Segment;
  /** printed under the dimension line, e.g. "1,496 cc · hybrid" */
  caption?: string;
  /** "FIG. 3" in the corner */
  fig?: string;
  /** small version for lists: no dimension line or labels */
  compact?: boolean;
  className?: string;
}

/** An ink side-elevation of a body style, in the style of a technical drawing. */
export function CarFigure({ segment, caption, fig, compact, className }: Props) {
  const s = SHAPES[segment];
  const label = `${SEGMENT_LABEL[segment]}${caption ? ` · ${caption}` : ""}`;
  const [m1, m2] = s.mirror;
  return (
    <svg
      viewBox={compact ? "10 18 304 118" : "0 0 320 160"}
      className={`fig${compact ? " fig-compact" : ""}${className ? ` ${className}` : ""}`}
      role="img"
      aria-label={`${label} outline drawing`}
    >
      <path className="fig-body" d={s.body} />
      {s.glass && <path className="fig-glass" d={s.glass} />}
      <path className="fig-line" d={s.lines} />
      <path className="fig-line" d={`M${m1} ${m2} l-6 -6 l-6 2 l4 4 Z`} />
      <path className="fig-line" d={`M${s.lamp - 4} 92 l8 0 l0 4`} />
      {s.wheels.map((x) => (
        <g key={x}>
          <path className="fig-arch" d={`M${x - 24} 112 A24 24 0 0 1 ${x + 24} 112`} />
          <circle className="fig-tyre" cx={x} cy={112} r={19} />
          <circle className="fig-rim" cx={x} cy={112} r={11} />
          <circle className="fig-rim" cx={x} cy={112} r={2.5} />
        </g>
      ))}
      <path className="fig-ground" d="M6 131.5 L314 131.5" />
      {!compact && (
        <>
          <path className="fig-dim" d={`M${s.wheels[0]} 142 L${s.wheels[1]} 142 M${s.wheels[0]} 137 L${s.wheels[0]} 147 M${s.wheels[1]} 137 L${s.wheels[1]} 147`} />
          <text className="fig-text" x={(s.wheels[0] + s.wheels[1]) / 2} y={156} textAnchor="middle">
            {label.toUpperCase()}
          </text>
          {fig && <text className="fig-text fig-tag" x={10} y={14}>{fig}</text>}
        </>
      )}
    </svg>
  );
}

/** Shared pattern defs; render once per page. */
export function CarFigureDefs() {
  return (
    <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true">
      <defs>
        <pattern id="fig-hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="5" height="5" fill="var(--slip)" />
          <line x1="0" y1="0" x2="0" y2="5" stroke="var(--hair)" strokeWidth="1.1" />
        </pattern>
      </defs>
    </svg>
  );
}
