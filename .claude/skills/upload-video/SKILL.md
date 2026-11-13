---
name: upload-video
description: Upload a generated skate clip to YouTube via the browser-automation uploader (YouTube Studio, no API/quota), or post one random unposted clip. Posts to a dedicated account. Use when the user runs /upload-video, or asks to upload/post a clip to YouTube.
---

# upload-video

Browser-automation YouTube uploader copied from the ChessPecker monorepo. Drives
YouTube Studio with Playwright (no Data API, no quota). Module lives in
`youtube_uploader/`; the nightly picker is `scripts/post_nightly.py`.

## Account

Posts as the dedicated channel **`ryanreed5151471885@gmail.com`** — its logged-in
browser profile is `youtube_uploader/profiles/ryanreed5151471885@gmail.com/`.
Cookies persist there. This account is used by this repo only (it was removed from
ChessPecker's rotation), so nothing else posts to the same channel.

Re-auth if the session dies:
`python youtube_uploader/login.py --profile ryanreed5151471885@gmail.com`
Check (headless): `python youtube_uploader/login.py --check --profile ryanreed5151471885@gmail.com`

## Invocation

```
/upload-video                 # upload 1 random unposted clip (same as the nightly job)
/upload-video <clip dir>      # upload exactly this clip (dir holding video.mp4 + metadata)
```

No argument = post one random clip via `scripts/post_nightly.py`.

## Clips

Clips come from `skate/output/<video>/clips/<clip>/`, each holding `video.mp4` and
`youtube_upload_metadata.json` (`post_title`, `post_description`), produced by
`/make_clips`. The uploader uses that metadata verbatim as the title/description.

## Steps

### Post one random clip (default)
```
python scripts/post_nightly.py            # add --dry-run to preview the pick
```
Picks a random clip whose dir is not yet in `posted.json`, uploads it, and records
it so it never double-posts. Relay stdout verbatim. Each upload drives a headless
browser and takes one to two minutes.

### Upload a specific clip
```
python youtube_uploader/upload.py \
  --video "skate/output/<video>/clips/<clip>/video.mp4" \
  --title "<post_title>" --description "<post_description>" \
  --profile ryanreed5151471885@gmail.com
```
Read the title/description from that clip's `youtube_upload_metadata.json`.
A specific-clip upload does NOT touch `posted.json` — only `post_nightly.py` records
to the ledger. Re-run it to intentionally repost.

Headless by default (`--headed` to watch). Publishes **Public**, not-for-kids.
Exit 0 + a `youtu.be` URL on success.

## Dedup

`posted.json` at the repo root maps each posted clip dir (repo-relative path) to its
upload record. `post_nightly.py` skips anything already in it. Delete a key to allow
a repost.

## On failure
- **No profile / session expired** (`AUTH_EXPIRED` in output) → re-run `login.py`
  for the account, confirm with `--check`.
- **Timed out** → open the newest `youtube_uploader/_debug/<run>/*.html` (per-step
  HTML, last 5 runs kept) to see what Studio showed, fix the selector in `upload.py`.

## Setup (once, if moving machines)
```
pip install -r youtube_uploader/requirements.txt
playwright install chromium
```

## Nightly job

Windows scheduled task **`skate_clip_nightly`** runs `scripts/post_nightly.py` once a
day at a random time between 3:00 and 6:00 AM (3h random delay on a 3 AM trigger).
One clip a night keeps a human cadence.

## Caveat

Re-uploading others' content risks Content ID claims, copyright strikes, and account
termination. Bans come from content + velocity, not the transport. One/night is
deliberately slow; the account is still at risk.
