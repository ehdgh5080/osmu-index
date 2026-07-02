# OSMU Optionality Index — data pipeline

Automates the two pieces the static prototype couldn't: **source-strength scoring**
and **pool growth**. It refreshes the index on a weekly schedule and rewrites the
website's data block, so the site stays live without hand-editing.

## What it does
1. **Seeds** (`seeds/candidates.csv`) — the un-adapted candidate pool. This is the
   list you grow. Each row: title, platform, chapters, optional rating, synopsis,
   fallback fit, payoff band, discovery flag.
2. **Live signals** (`osmu/trends.py`) — Google Trends interest + momentum per title
   (search interest as a reach/momentum proxy).
3. **Format fit** (`osmu/fit_llm.py`) — Claude scores drama/film/anime fit from the
   **synopsis only, no genre label** (the non-circular method the index was validated on).
4. **Scoring** (`osmu/score.py`) — the exact site formulas:
   `Source = .40·Reach + .25·Engagement + .20·Scale + .15·Momentum`,
   `Optionality = Σ(fit·audience weight)/2.55`, then the Source×Optionality quadrant.
5. **Output** — writes `data.json` and rewrites the `DATA:START…DATA:END` block in
   `site/index.html` (put your site there).

## Setup
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...        # optional; without it, seed fit is used
cp /path/to/index.html site/index.html     # the website to patch
python -m osmu.build
```
Automated weekly run: add `ANTHROPIC_API_KEY` as a repo secret; the GitHub Action
in `.github/workflows/update.yml` handles the cron + commit.

## Growing the pool
Add rows to `seeds/candidates.csv`. That's the whole job — everything else is
computed. To semi-automate discovery of *new* candidates, scrape a public ranking
page and append rows (see "Honest limits").

## Honest limits (read this)
- **No view-count scraping.** Naver/Kakao have no public API, render dynamically, and
  scraping raw view counts risks ToS violation and IP blocks. We use Google Trends
  interest as a *proxy* instead — legal and reproducible, but noisier than true reads.
- **Trends is a proxy, not truth.** Search interest ≠ readership. Treat Source as a
  comparative signal, not a measurement.
- **pytrends is unofficial** and can rate-limit; failures fall back to seed values.
- **Adaptation status** ("no screen deal yet") can't be verified reliably by machine.
  Keep it in the seed (`disc` column) and review periodically.
- **Candidate discovery isn't fully automated.** Growing the seed list from live
  rankings is left as a scraper you maintain, because ranking pages change markup and
  block bots. The scoring half *is* automated.

This pipeline makes the index **reproducible and self-updating on a maintained seed
list** — not an omniscient crawler. That boundary is deliberate and honest.
