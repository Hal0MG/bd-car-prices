"""Download the Bikroy used-car dataset and check it against its published hash.

Run: .venv/Scripts/python.exe scripts/download_data.py

Source: Amik, Momen and Lanard, "Car Dataset: Used cars data from Bikroy.com",
Mendeley Data, v2, CC BY 4.0, doi:10.17632/fmb4xmp4k5.2
"""

import hashlib
import sys
import urllib.request
from pathlib import Path

URL = (
    "https://data.mendeley.com/public-files/datasets/fmb4xmp4k5/files/"
    "7c689cb5-3d66-4450-b7f6-14d8ba5b3955/file_downloaded"
)
SHA256 = "cec972d4cf707424115d7d965ea3355d267c45f80543f82a1c3482c27e907e69"
DEST = Path(__file__).resolve().parents[1] / "data" / "raw" / "mendeley" / "car_dataset.csv"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if DEST.exists() and sha256(DEST) == SHA256:
        print(f"Already downloaded and verified: {DEST}")
        return 0

    DEST.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(URL, headers={"User-Agent": "shotti-ml/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        DEST.write_bytes(response.read())

    got = sha256(DEST)
    if got != SHA256:
        DEST.unlink()
        print(f"Hash mismatch, file removed.\n  expected {SHA256}\n  got      {got}")
        return 1
    print(f"Downloaded and verified: {DEST} ({DEST.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
