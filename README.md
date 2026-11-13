# viral_vid_maker

> Turn long-form YouTube videos into captioned vertical shorts and auto-post one to YouTube every night — all locally, no paid APIs.

This repo is a small pipeline wrapped around an open-source clipping engine:

1. **`/make_clips`** — point it at a YouTube URL. It downloads the video, transcribes it locally, has Claude pick the most clippable moments, renders vertical captioned clips, and writes per-clip upload metadata.
2. **`youtube_uploader/`** — browser-automation YouTube uploader (drives YouTube Studio with Playwright, no Data API or quota).
3. **`/upload-video`** — upload a clip, or post one random unposted clip, to a dedicated channel.
4. **Nightly job** — a Windows scheduled task posts one random clip at a random time between 3-6 AM, deduped so nothing posts twice.

The [`skate`](https://github.com/r2hu1/skate) CLI (faster-whisper + OpenCV + FFmpeg) is the clipping engine underneath, vendored in `src/` and `skate/`. It does transcription, face-tracked cropping, and rendering. **Clip ranking was moved off the local LLM to Claude** — the local model picked weak moments — so `/make_clips` dumps transcript chunks, Claude ranks them, and the picks are fed back into skate's render step.

---

## Pipeline: `/make_clips <youtube-url>`

```
URL → yt-dlp download → faster-whisper transcribe (GPU) → chunk transcript
    → Claude ranks chunks for clippability → render vertical + MrBeast captions
    → finalize into clips/<slug>/{video.mp4, youtube_upload_metadata.json, captions.srt}
```

Output per clip (`skate/output/<video>/clips/<clip-slug>/`):

| File | Contents |
| --- | --- |
| `video.mp4` | 1080×1920 vertical, face-tracked crop, captions burned in |
| `youtube_upload_metadata.json` | `post_title`, `post_description`, `generated_at_timestamp` |
| `captions.srt` | plain captions |

The skill definition and its helper scripts live in `.claude/skills/make_clips/`.

---

## Uploading

Posts to the dedicated channel **`ryanreed5151471885@gmail.com`**. Its logged-in
browser profile lives in `youtube_uploader/profiles/` (git-ignored — it holds live
session cookies; **never commit it**).

```bash
# one random unposted clip (what the nightly job runs)
python scripts/post_nightly.py              # --dry-run to preview the pick

# a specific clip
python youtube_uploader/upload.py \
  --video "skate/output/<video>/clips/<clip>/video.mp4" \
  --title "..." --description "..." --profile ryanreed5151471885@gmail.com
```

Headless by default, publishes Public / not-for-kids. See `.claude/skills/upload-video/`.

### Dedup

`posted.json` (repo root, git-ignored) maps each posted clip dir to its upload
record. `post_nightly.py` skips anything already in it, so no clip posts twice.

### Nightly auto-post

Windows scheduled task **`viral_vid_maker_nightly`**: daily 3 AM trigger + 3-hour
random delay, so it fires once at a random time between 3-6 AM. One clip a night.

---

## Setup

```bash
bun install                                       # engine deps
python -m pip install -r youtube_uploader/requirements.txt   # uploader (Playwright)
# skate's own Python env (faster-whisper + OpenCV) is at ~/.skate/venv via `skate setup`
```

Config for the clipping engine is at `~/.skate/config.json` (clips count, min/max
length, crop, output dirs).

---

## Caveat

Re-uploading others' content risks Content ID claims, copyright strikes, and
account termination. Bans come from content and posting velocity, not the transport.
One clip a night is a deliberately slow, human cadence; the account is still at risk.

---

## Credits

Clipping engine: [r2hu1/skate](https://github.com/r2hu1/skate) (MIT). Uploader
module adapted from a private browser-automation uploader.
