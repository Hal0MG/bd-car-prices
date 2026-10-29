"use client";

import { useEffect, useState } from "react";
import { t } from "@/lib/i18n/en";
import { installClickSounds, setSound, SOUND_EVENT, soundOn } from "@/lib/sound";

/** Turns the site's sounds on and off. Every copy stays in step, so the intro's and the masthead's agree. */
export function SoundToggle({ className = "" }: { className?: string }) {
  const [on, setOn] = useState<boolean | null>(null);
  useEffect(() => {
    installClickSounds();
    const sync = () => setOn(soundOn());
    sync();
    addEventListener(SOUND_EVENT, sync);
    return () => removeEventListener(SOUND_EVENT, sync);
  }, []);
  if (on === null) return <span className={`sound-toggle ${className}`} aria-hidden="true" />;
  return (
    <button type="button" className={`sound-toggle ${className}`} onClick={() => setSound(!on)} aria-label={t.sound.label} aria-pressed={on}>
      {on ? t.sound.on : t.sound.off}
    </button>
  );
}
