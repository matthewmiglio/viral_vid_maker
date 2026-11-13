---
name: make_clips
description: Turn a YouTube URL into short vertical viral clips (20-60s), ranked by Claude. Use when the user runs /make_clips <youtube-url>, or asks to generate viral/short clips from a YouTube video. Infers the video type (podcast, interview, talking-head, gameplay, etc.), transcribes on GPU, has Claude pick the clippable moments, then renders vertical clips with burned captions into per-clip folders with YouTube upload metadata.
---

# make_clips

Turn one YouTube URL into short vertical clips. The ranking is done by **Claude reading the transcript** (local LLMs are too weak and pick random moments). Clips are chosen to match the video type.

## Fixed environment (this machine)

- Repo root: `M:\my_files\my_programsiral_vid_maker`
- Bun: `C:\Users\matt\.bun\bin\bun.exe`
- venv python: `C:\Users\matt\.skate\venv\Scripts\python.exe` (invoke as `python -I <script>`)
- Always export before any `bun`/skate call: `HF_HOME=/e/skate/hf` and `TMPDIR=/e/skate/tmp` (keeps model + temp off the nearly-full C: drive).
- Analysis cache: `C:\Users\matt\.skate\cache\<slug>-analysis.json`
- Downloaded video: `M:\my_files\my_programsiral_vid_maker\skate\temp\<slug>\<ID>.webm`
- Output: `M:\my_files\my_programsiral_vid_maker\skate\output\<slug>\`
- `<slug>` = the lowercased YouTube video id (e.g. `VCjT35E0RBY` -> `vcjt35e0rby`).
- Scripts for this skill are in this skill's `scripts/` folder.

Run `bun`/python from Git Bash (the Bash tool), so coreutils (`mv`/`rm`) resolve.

## Steps

### 1. Parse input
Take the YouTube URL from the args. Extract the 11-char video id (the `v=` param, or the path segment). `<slug>` = id lowercased.

### 2. Check the type early (metadata)
Get the title/category without downloading:
```
yt-dlp --skip-download --print "%(duration>%H:%M:%S)s | %(categories)s | %(title)s" "<url>"
```
Classify into one of:
- **Conversational** - podcast, interview, talking-head, monologue, vlog, commentary, lecture. **The reliable path.**
- **Visual-driven** - gameplay, sports, music video, highlights, anything where the viral moment is on screen, not spoken.

If **visual-driven**, tell the user plainly: transcript-based ranking is weak for this type because the moments are visual, not spoken, so results will be hit-or-miss. Ask whether to proceed anyway or stop. (A proper fix is an audio-loudness + motion scorer, not built yet.)

### 3. Ensure clip-length config
Make sure `C:\Users\matt\.skate\config.json` has `"minLength": 20, "maxLength": 60, "crop": true`. Edit it if not.

### 4. Transcribe + chunk (no local ranking)
```
cd M:/my_files/my_programs/viral_vid_maker
export HF_HOME=/e/skate/hf TMPDIR=/e/skate/tmp SKATE_SKIP_AI_RANK=1
C:/Users/matt/.bun/bin/bun.exe run src/index.ts analyze "<url>"
```
`SKATE_SKIP_AI_RANK=1` skips the local LLM. This downloads, transcribes on GPU, and chunks. Run it in the background (it's long for multi-hour videos) and wait for completion.

### 5. Dump chunks for ranking
```
C:/Users/matt/.skate/venv/Scripts/python.exe -I <skill>/scripts/dump_chunks.py \
  "C:/Users/matt/.skate/cache/<slug>-analysis.json" \
  "<scratchpad>/chunks_<slug>.txt"
```
Read that file. Each line is `index <tab> start <tab> end <tab> dur <tab> text`.

### 6. Rank with Claude (the core step)
Read every chunk. Pick the **8 best** standalone clips (or the count the user asked for), each with duration **20-60s** (only pick chunks whose `dur` is <= 60). Spread them across the **whole runtime** - do not cluster at the start.

What makes a good clip depends on type:
- **Podcast / interview / talking-head / commentary:** a surprising or counterintuitive claim, a strong or controversial opinion stated with conviction, a personal story with a payoff or twist, a genuinely funny bit, a heated/emotional exchange, a concrete reveal (a number, a secret, a name). The first line is the hook - if the opening line is boring, skip it. It must start at the top of a thought and end on the payoff, not mid-sentence.
- Avoid: intros/greetings, sponsor reads, logistics, vague musing, back-and-forth filler, anything that only makes sense with more context.

For each pick write a `post_title` (the scroll-stopping hook, no clickbait lies) and a `post_description` (1-2 sentences for the YouTube/Shorts description, may include a few hashtags). Write them to a picks file:
```json
[
  {"index": 51, "score": 9, "post_title": "The biggest animals ever are alive RIGHT NOW",
   "post_description": "Paleontologist Kenneth Lacovara on why the blue whale and redwoods are the largest life in Earth's history. #science #dinosaurs"},
  ...
]
```
Save as `<scratchpad>/picks_<slug>.json`.

### 7. Inject picks
```
C:/Users/matt/.skate/venv/Scripts/python.exe -I <skill>/scripts/apply_picks.py \
  "C:/Users/matt/.skate/cache/<slug>-analysis.json" \
  "<scratchpad>/picks_<slug>.json" \
  "M:/my_files/my_programs/viral_vid_maker/skate/temp/<slug>/<ID>.webm"
```
(Find the exact `<ID>.webm` with `ls skate/temp/<slug>/*.webm`.)

### 8. Render (face-track + fill crop + burned captions)
```
cd M:/my_files/my_programs/viral_vid_maker
export HF_HOME=/e/skate/hf TMPDIR=/e/skate/tmp
C:/Users/matt/.bun/bin/bun.exe run src/index.ts render "M:/my_files/my_programs/viral_vid_maker/skate/temp/<slug>/<ID>.webm"
```
Vertical 1080x1920, crop follows the speaker, never letterboxes. Captions are the baked-in "MrBeast" style (big bold yellow, uppercase, centered, heavy black outline) defined in `src/core/subtitles.ts`.

### 9. Finalize into per-clip folders
```
C:/Users/matt/.skate/venv/Scripts/python.exe -I <skill>/scripts/finalize_output.py \
  "M:/my_files/my_programs/viral_vid_maker/skate/output/<slug>" \
  "C:/Users/matt/.skate/cache/<slug>-analysis.json.picks.json"
```
Produces, per clip:
```
skate/output/<slug>/clips/<clip_slug>/video.mp4
skate/output/<slug>/clips/<clip_slug>/youtube_upload_metadata.json   # {post_title, post_description, generated_at_timestamp}
skate/output/<slug>/clips/<clip_slug>/captions.srt                   # bonus
```

### 10. Report
Give the user: original length, video type, number of clips, where they are, and the list of clip titles with timestamps. Do not auto-open anything unless asked.

## Notes
- Re-running is cheap: the transcript is cached, so steps 4 is skipped on a re-run (it prints "Using cached transcript"). You can re-rank (6-9) without re-downloading.
- If a download exceeds Skate's 5-min timeout on a very large video, raise the timeout in `src/core/downloader.ts`.
- Clip count, min/max length are the only knobs; default 8 clips, 20-60s.
