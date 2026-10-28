import type { CSSProperties } from "react";

// Number plates built in HTML so they stay sharp at any size, modelled on real ones:
// a Yokohama private plate (green on white) and a Dhaka Metro plate (black on white, heavy border).

export function JapanPlate({ style }: { style?: CSSProperties }) {
  return (
    <div className="plate jp" role="img" aria-label="Japanese number plate, Yokohama" style={style}>
      <i className="bolt" /><i className="bolt" />
      <div className="t top">横浜<span>330</span></div>
      <div className="kana">さ</div>
      <div className="t big">38-88</div>
    </div>
  );
}

/** ঘ is the BRTA series for jeeps and SUVs, which is how a Prado is registered. */
export function DhakaPlate({ style }: { style?: CSSProperties }) {
  return (
    <div className="plate bd" role="img" aria-label="Dhaka Metro number plate" style={style}>
      <i className="bolt" /><i className="bolt" />
      <div className="t top">ঢাকা মেট্রো-ঘ</div>
      <div className="t big">১৭-৫৮৬২</div>
      <i className="holo" />
      <span className="serial">BRTA</span>
    </div>
  );
}
