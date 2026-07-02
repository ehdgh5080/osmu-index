"""Live-signal stub.

We tried Google Trends (pytrends) as a live reach/momentum proxy, but Google
now returns HTTP 429 to pytrends from essentially all environments (it's an
unofficial, blocked endpoint). Rather than a pipeline that fails intermittently,
source signals come from curated public-research values in seeds/candidates.csv
(reach/eng/scale/mom columns), which is stable and fully reproducible.

This module is kept as a no-op so the interface stays intact; if a reliable
trends source (e.g. a paid API) is added later, implement it here.
"""
from typing import Optional


def _client():
    return None


def interest(kr: str = "", en: str = "", override: str = "", pytrends=None) -> Optional[dict]:
    return None
