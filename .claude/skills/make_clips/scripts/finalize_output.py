"""Restructure Skate render output into per-clip folders for YouTube upload.

Usage: python -I finalize_output.py <output_video_dir> <cache.picks.json>

Produces, for each clip:
  <output_video_dir>/clips/<clip_slug>/video.mp4
  <output_video_dir>/clips/<clip_slug>/youtube_upload_metadata.json
  <output_video_dir>/clips/<clip_slug>/captions.srt   (bonus, if present)

youtube_upload_metadata.json = {post_title, post_description, generated_at_timestamp}
clip_slug is derived from the post_title.
"""
import json, os, re, shutil, sys
from datetime import datetime

out_dir, picks_path = sys.argv[1], sys.argv[2]
clips_dir = os.path.join(out_dir, "clips")
caps_dir = os.path.join(out_dir, "captions")
meta = json.load(open(os.path.join(out_dir, "metadata.json"), encoding="utf-8"))
picks = json.load(open(picks_path, encoding="utf-8")) if os.path.exists(picks_path) else []


def slugify(s, maxlen=60):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (s or "clip").lower()).strip("-")
    return (s[:maxlen].rstrip("-")) or "clip"


def find_pick(start):
    best, bd = None, 2.0
    for p in picks:
        dd = abs(p.get("start", -999) - start)
        if dd < bd:
            best, bd = p, dd
    return best or {}


now = datetime.now().astimezone().isoformat()
used = set()
made = []
for i, m in enumerate(meta, 1):
    clip_mp4 = os.path.join(clips_dir, m.get("clipFile", f"clip-{i:02d}.mp4"))
    if not os.path.exists(clip_mp4):
        print(f"WARN: missing {clip_mp4}"); continue
    pick = find_pick(m.get("start", -1))
    title = pick.get("post_title") or m.get("title") or f"Clip {i}"
    desc = pick.get("post_description") or ""
    slug = slugify(title)
    base = slug
    n = 2
    while slug in used:
        slug = f"{base}-{n}"; n += 1
    used.add(slug)

    folder = os.path.join(clips_dir, slug)
    os.makedirs(folder, exist_ok=True)
    shutil.move(clip_mp4, os.path.join(folder, "video.mp4"))
    srt = os.path.join(caps_dir, m.get("subtitleFile", f"clip-{i:02d}.srt"))
    if os.path.exists(srt):
        shutil.copy(srt, os.path.join(folder, "captions.srt"))
    json.dump({"post_title": title, "post_description": desc,
               "generated_at_timestamp": now},
              open(os.path.join(folder, "youtube_upload_metadata.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    made.append(slug)

# tidy: drop the now-empty flat captions dir and any leftover flat clip files
for f in os.listdir(clips_dir):
    p = os.path.join(clips_dir, f)
    if os.path.isfile(p) and f.endswith((".mp4", ".srt")):
        os.remove(p)
if os.path.isdir(caps_dir):
    shutil.rmtree(caps_dir, ignore_errors=True)

print(f"finalized {len(made)} clips:")
for s in made:
    print("  " + s)
