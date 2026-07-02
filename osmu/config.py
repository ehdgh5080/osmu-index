"""Model constants — MUST stay in sync with the website's index.html."""

# Source strength = weighted sum of four 0-100 component signals
SRC_WEIGHTS = {"reach": 0.40, "eng": 0.25, "scale": 0.20, "mom": 0.15}

# Optionality = audience-weighted format fit
FMT_WEIGHTS = {"drama": 1.0, "film": 0.70, "anime": 0.85}
FMT_WSUM = sum(FMT_WEIGHTS.values())  # 2.55
VIABLE_FIT = 70  # a format "opens" if fit >= this

# Claude model for synopsis-based format-fit scoring
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# Files
SEED_CANDIDATES = "seeds/candidates.csv"
SEED_VALIDATION = "seeds/validation.json"
OUT_JSON = "data.json"
# Path to the website file whose DATA block gets patched (relative to repo root)
SITE_INDEX = "site/index.html"
