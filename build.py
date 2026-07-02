"""Orchestrate: seed candidates -> live signals -> scores -> data.json (+ patch site).

Run:  python -m osmu.build
Env:  ANTHROPIC_API_KEY (for format-fit; optional — falls back to seed fit if absent)
"""
import csv
import json
import re
import sys
from pathlib import Path

from . import config, score
from .trends import interest, _client
from .fit_llm import score_fit


def load_candidates(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r.get("name"):
                continue
            r["chapters"] = int(r["chapters"]) if r.get("chapters") else 0
            r["rating"] = float(r["rating"]) if r.get("rating") else None
            r["disc"] = str(r.get("disc", "")).strip().lower() in ("1", "true", "yes")
            r["seed_fit"] = [int(x) for x in r["seed_fit"].split("|")] if r.get("seed_fit") else None
            r["band"] = [int(x) for x in r["band"].split("|")] if r.get("band") else [50, 80]
            rows.append(r)
    return rows


def collect(cands):
    """Attach live Trends signals + LLM fit to each candidate."""
    py = _client()
    for c in cands:
        tr = interest(c.get("kr") or c["name"], py) or {}
        c["_peak"] = tr.get("peak")
        c["_recent"] = tr.get("recent")
        c["_slope"] = tr.get("slope")
        fit = score_fit(c["synopsis"]) if c.get("synopsis") else None
        c["fit"] = fit or c["seed_fit"] or [70, 70, 70]
        print(f"  {c['name']:<38} trends_peak={c['_peak']} slope={c['_slope']} fit={c['fit']}")
    return cands


def build_forward(cands):
    peaks = [c["_peak"] for c in cands if c["_peak"] is not None]
    recents = [c["_recent"] for c in cands if c["_recent"] is not None]
    out = []
    for c in cands:
        comp = [
            score.reach_score(c["_peak"], peaks),
            score.eng_score(c["rating"], c["_recent"], recents),
            score.scale_score(c["chapters"]),
            score.momentum_score(c["_slope"]),
        ]
        item = {
            "n": c["name"], "kr": c.get("kr", ""), "kind": "forward",
            "comp": comp, "fit": c["fit"], "band": c["band"],
            "foot": c.get("foot", ""),
        }
        if c["disc"]:
            item["disc"] = True
        else:
            item["stat"] = c.get("stat", "in progress")
        item["src"] = score.source_strength(comp)
        item["o"] = score.optionality(c["fit"])
        out.append(item)
    return out


def patch_site(all_titles):
    """Rewrite the DATA:START..DATA:END block inside the site's index.html."""
    p = Path(config.SITE_INDEX)
    if not p.exists():
        print(f"  (site file {p} not found — skipping patch)")
        return
    html = p.read_text(encoding="utf-8")
    lines = ["/* DATA:START (pipeline-generated — edit seeds/, not here) */", "const DATA=["]
    for t in all_titles:
        lines.append("  " + json.dumps(t, ensure_ascii=False) + ",")
    lines += ["];", "/* DATA:END */"]
    block = "\n".join(lines)
    new = re.sub(r"/\* DATA:START.*?/\* DATA:END \*/", block, html, count=1, flags=re.S)
    p.write_text(new, encoding="utf-8")
    print(f"  patched {p}")


def main():
    root = Path(__file__).resolve().parent.parent
    import os
    os.chdir(root)
    print("1) load seeds")
    cands = load_candidates(config.SEED_CANDIDATES)
    validation = json.loads(Path(config.SEED_VALIDATION).read_text(encoding="utf-8"))
    print(f"   {len(cands)} candidates, {len(validation)} validation titles")

    print("2) collect live signals (Google Trends + Claude fit)")
    collect(cands)

    print("3) score")
    forward = build_forward(cands)
    # validation titles already carry src/o/fit (static backtest set)
    for v in validation:
        v.setdefault("o", score.optionality(v["fit"]))
    all_titles = forward + validation

    src_t, opt_t = score.thresholds(all_titles)
    for t in all_titles:
        t_q = score.quadrant(t["src"], t["o"], src_t, opt_t)
    print(f"   thresholds SRC_T={src_t} OPT_T={opt_t}")

    print("4) write data.json + patch site")
    Path(config.OUT_JSON).write_text(
        json.dumps({"generated": __import__("datetime").date.today().isoformat(),
                    "src_t": src_t, "opt_t": opt_t, "titles": all_titles},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    patch_site(all_titles)
    print("done.")


if __name__ == "__main__":
    sys.exit(main())
