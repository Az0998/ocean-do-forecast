"""Shared HTTPS download helper (curl first, urllib fallback)."""
from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.request import Request, urlopen


def download(url: str, dest: Path, min_bytes: int = 1_000_000, chunk: int = 1 << 20) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size >= min_bytes:
        print(f"[dl] exists, skip: {dest}", flush=True)
        return dest
    print(f"[dl] curl: {url}", flush=True)
    try:
        subprocess.check_call(
            ["curl", "-L", "--retry", "3", "-C", "-", "-o", str(dest), url]
        )
        if dest.exists() and dest.stat().st_size >= min_bytes:
            return dest
    except Exception as exc:
        print(f"[dl] curl failed ({exc}); urllib fallback", flush=True)
    req = Request(url, headers={"User-Agent": "ocean-do-forecast/0.2"})
    with urlopen(req, timeout=600) as resp, open(dest, "wb") as f:
        total = resp.headers.get("Content-Length")
        total = int(total) if total else None
        done = 0
        while True:
            buf = resp.read(chunk)
            if not buf:
                break
            f.write(buf)
            done += len(buf)
            if total and done % (8 * chunk) < chunk:
                print(f"[dl] {100.0 * done / total:5.1f}%", flush=True)
    return dest
