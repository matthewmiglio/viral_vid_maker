#!/usr/bin/env python
"""Post one random unposted clip to YouTube using its generated metadata.

Walks the skate clip tree (skate/output/<video>/clips/<clip>/video.mp4), reads the
sibling youtube_upload_metadata.json for the title/description, picks a random clip
not already in the ledger, and uploads it via the copied youtube_uploader module.

Usage: python scripts/post_nightly.py [--profile EMAIL] [--dry-run]
"""
import argparse
import json
import random
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLIP_GLOB = "skate/output/*/clips/*/video.mp4"
UPLOADER = REPO / "youtube_uploader" / "upload.py"
LEDGER = REPO / "posted.json"
LOGS = REPO / "logs"
DEFAULT_PROFILE = "ryanreed5151471885@gmail.com"
URL_RE = re.compile(r"https?://(?:youtu\.be/|(?:www\.)?youtube\.com/)\S+")


def load_ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}


def clip_key(video: Path) -> str:
    """Stable dedup key: the clip dir path relative to the repo, forward slashes."""
    return video.parent.relative_to(REPO).as_posix()


def meta_for(video: Path):
    f = video.parent / "youtube_upload_metadata.json"
    if not f.exists():
        return None
    m = json.loads(f.read_text(encoding="utf-8"))
    title = (m.get("post_title") or "").strip()
    return {"title": title, "description": (m.get("post_description") or "").strip()} if title else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=DEFAULT_PROFILE)
    ap.add_argument("--dry-run", action="store_true", help="pick and print, don't upload")
    args = ap.parse_args()

    LOGS.mkdir(exist_ok=True)
    started = datetime.now()
    posted = load_ledger()

    candidates = [v for v in REPO.glob(CLIP_GLOB)
                  if clip_key(v) not in posted and meta_for(v)]
    if not candidates:
        print("no unposted clips with metadata left")
        return

    video = random.choice(candidates)
    key = clip_key(video)
    meta = meta_for(video)
    print(f"posting {key}\n  title: {meta['title']!r}\n  profile: {args.profile}")

    if args.dry_run:
        print(f"(dry-run) {len(candidates)} candidates available")
        return

    log = LOGS / f"nightly_{started:%Y-%m-%d_%H%M%S}.log"
    r = subprocess.run(
        [sys.executable, str(UPLOADER), "--video", str(video),
         "--title", meta["title"], "--description", meta["description"],
         "--profile", args.profile],
        capture_output=True, text=True, encoding="utf-8",
    )
    out = (r.stdout or "") + (r.stderr or "")
    print(out)
    url = (URL_RE.search(out) or [None])[0] if URL_RE.search(out) else None

    record = {"clip": key, "title": meta["title"], "profile": args.profile, "url": url,
              "posted_at": started.isoformat(timespec="seconds"), "exit_code": r.returncode}
    log.write_text(json.dumps(record, ensure_ascii=False, indent=2)
                   + "\n\n--- uploader output ---\n" + out, encoding="utf-8")

    if r.returncode == 0:
        posted[key] = record  # dedup key; never reposts the same clip
        LEDGER.write_text(json.dumps(posted, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"posted + recorded -> {url or '(no url parsed)'}  | log: {log}")
    else:
        print(f"upload failed (exit {r.returncode}); not recording | log: {log}")
        sys.exit(1)


if __name__ == "__main__":
    main()
