"""Dump a Skate analysis cache's transcript chunks as compact lines for ranking.
Usage: python -I dump_chunks.py <analysis_cache.json> <out.txt>
Each line: index <TAB> start(s) <TAB> end(s) <TAB> dur <TAB> text[:320]
"""
import json, sys

cache, out = sys.argv[1], sys.argv[2]
d = json.load(open(cache, encoding="utf-8"))
lines = []
for c in d.get("chunks", []):
    k = c.get("chunk", {})
    st, en = k.get("start", 0), k.get("end", 0)
    txt = " ".join(k.get("text", "").split())
    lines.append(f'{c.get("index")}\t{st:.0f}\t{en:.0f}\t{en-st:.0f}s\t{txt[:320]}')
open(out, "w", encoding="utf-8").write("\n".join(lines))
print(f"{len(lines)} chunks -> {out}")
