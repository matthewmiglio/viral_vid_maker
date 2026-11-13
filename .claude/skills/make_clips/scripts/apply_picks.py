"""Inject Claude-chosen clip picks into a Skate analysis cache, ready for `skate render`.

Usage: python -I apply_picks.py <analysis_cache.json> <picks.json> <source_video_path>

picks.json: [{"index": <chunk index>, "score": <0-10>,
              "post_title": "...", "post_description": "..."}, ...]

Writes the cache's `selected` (full chunk objects, with aiScore), `ranked`, and sets
`sourceFile` to the local video. Also writes a sidecar <cache>.picks.json carrying the
post_title / post_description per pick (keyed by start time) for finalize_output.py.
"""
import json, sys

cache, picks_path, source = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(cache, encoding="utf-8"))
picks = json.load(open(picks_path, encoding="utf-8"))
by_index = {c["index"]: c for c in d["chunks"]}

selected, ranked, sidecar = [], [], []
for p in picks:
    idx = p["index"]
    if idx not in by_index:
        print(f"WARN: index {idx} not found, skipping"); continue
    c = json.loads(json.dumps(by_index[idx]))  # deep copy
    c["aiScore"] = p.get("score", 0)
    selected.append(c)
    st, en = c["chunk"]["start"], c["chunk"]["end"]
    ranked.append({"index": idx, "title": p.get("post_title", ""), "score": p.get("score", 0),
                   "start": st, "end": en, "reason": p.get("post_title", "")})
    sidecar.append({"start": st, "end": en,
                    "post_title": p.get("post_title", ""),
                    "post_description": p.get("post_description", "")})

selected.sort(key=lambda c: -c["aiScore"])
ranked.sort(key=lambda r: -r["score"])
d["selected"], d["ranked"], d["sourceFile"] = selected, ranked, source
json.dump(d, open(cache, "w", encoding="utf-8"))
json.dump(sidecar, open(cache + ".picks.json", "w", encoding="utf-8"))
print(f"injected {len(selected)} picks; sourceFile={source}")
