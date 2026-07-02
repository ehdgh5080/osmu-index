"""Live public signal: Google Trends interest + momentum.

This is the automatable, ToS-friendly signal source. We do NOT scrape
Naver/Kakao view counts (no public API, dynamic rendering, ToS/IP-block risk).
Instead we use search interest as a reach/momentum proxy.

pytrends is unofficial and can rate-limit; every call is wrapped so a failure
degrades gracefully to None (the scorer then falls back to seed values).
"""
import time
from typing import Optional

try:
    from pytrends.request import TrendReq
except Exception:  # pytrends not installed / import issue
    TrendReq = None


def _client():
    if TrendReq is None:
        return None
    try:
        return TrendReq(hl="ko-KR", tz=540)
    except Exception:
        return None


def interest(keyword: str, pytrends=None) -> Optional[dict]:
    """Return {'peak','recent','prior','slope'} of 12-month weekly interest, or None."""
    py = pytrends or _client()
    if py is None:
        return None
    try:
        py.build_payload([keyword], timeframe="today 12-m", geo="KR")
        df = py.interest_over_time()
        if df is None or df.empty or keyword not in df:
            return None
        s = df[keyword].tolist()
        if len(s) < 16:
            return None
        peak = max(s) or 1
        recent = sum(s[-8:]) / 8.0
        prior = sum(s[-16:-8]) / 8.0 or 1.0
        return {"peak": peak, "recent": recent, "prior": prior, "slope": recent / prior}
    except Exception:
        return None
    finally:
        time.sleep(2)  # be polite / avoid rate limit
