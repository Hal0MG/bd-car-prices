"""Copy every catalogue photo from Wikimedia Commons into web/public/cars, in three sizes.

Run from the web/ folder:  python scripts/localize_photos.py
Reads the entries in src/lib/photos.ts (each carries the Commons thumbnail URL it was chosen from),
downloads each distinct file once, politely, and writes <id>-120.jpg, <id>-360.jpg and <id>-960.jpg,
where <id> is the Commons file name slugified the same way as slugify() in src/lib/format.ts.
Files already on disk are skipped, so a rerun only fetches new cars. Credits stay in photos.ts and
on every page; only the hosting moves, so the site no longer depends on Wikimedia serving images
at visitors' request.
"""

import io
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image

WEB = Path(__file__).resolve().parents[1]
OUT = WEB / "public" / "cars"
UA = {"User-Agent": "ShottiDam/0.1 (https://github.com/Hal0MG/bd-car-prices; photo hosting)"}
SIZES = (120, 360, 960)


def slugify(s: str) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", s.lower()))


def photo_id(file: str) -> str:
    return slugify(re.sub(r"\.[^.]+$", "", file))


def entries() -> dict[str, dict]:
    text = (WEB / "src" / "lib" / "photos.ts").read_text(encoding="utf-8")
    found = re.findall(r'^\s*"([^"]+)": (\{.*\}),\s*$', text, re.M)
    return {k: json.loads(v) for k, v in found}


def fetch(url: str) -> bytes:
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read()
        except Exception as e:  # 429 and flaky connections: back off and retry
            time.sleep(4 * (attempt + 1))
            last = e
    raise RuntimeError(f"{url}: {last}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    done = skipped = 0
    for key, p in entries().items():
        pid = photo_id(p["file"])
        if pid in seen:
            continue
        seen.add(pid)
        if all((OUT / f"{pid}-{w}.jpg").exists() for w in SIZES):
            skipped += 1
            continue
        im = Image.open(io.BytesIO(fetch(p["src"]))).convert("RGB")
        for w in SIZES:
            h = round(im.height * w / im.width)
            im.resize((w, h), Image.LANCZOS).save(OUT / f"{pid}-{w}.jpg", "JPEG", quality=80, optimize=True, progressive=True)
        done += 1
        time.sleep(0.4)
        print(f"{key}: {pid}", flush=True)
    print(f"{done} downloaded, {skipped} already there, {len(seen)} photos in all")
    return 0


if __name__ == "__main__":
    sys.exit(main())
