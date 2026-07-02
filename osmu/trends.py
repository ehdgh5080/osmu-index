"""Live public signal: Google Trends interest + momentum.

Automatable, ToS-friendly. We do NOT scrape Naver/Kakao view counts.
Search interest is used as a reach/momentum proxy.

Keyword robustness: a single KR title often returns empty (too short/common,
or the audience searches in English). So we try several keywords in order and
keep the first that returns usable data:
  1) an explicit override (trend_kw from the seed)
  2) the Korean title
  3) the English title
  4) English title + " 웹툰"  (disambiguates common words)
pytrends is unofficial and can rate-limit; failures degrade to None.
"""
import time
from typing import Optional

try:
    from pytrends.request import TrendReq
except Exception:
    TrendReq = None


def _client():
    if TrendReq is None:
        return None
    try:
        return TrendReq(hl="ko-KR", tz=540, retries=2, backoff_factor=0.5)
    except Exception:
        return None


def _query_one(py, keyword: str, geo: str) -> Optional[dict]:
    try:
        py.build_payload([keyword], timeframe="today 12-m", geo=geo)
        df = py.interest_over_time()
        if df is None or df.empty or keyword not in df:
            return None
        s = df[keyword].tolist()
        if len(s) < 16 or max(s) == 0:
            return None
        peak = max(s)
        recent = sum(s[-8:]) / 8.0
        prior = sum(s[-16:-8]) / 8.0 or 1.0
        return {"peak": peak, "recent": recent, "prior": prior,
                "slope": recent / prior, "kw": keyword, "geo": geo or "WW"}
    except Exception:
        return None
    finally:
        time.sleep(2)  # be polite / avoid rate limit


def interest(kr: str = "", en: str = "", override: str = "", pytrends=None) -> Optional[dict]:
    """Try several keywords/regions; return the first usable signal, else None.

    Strategy: KR title (Korea) -> override -> EN title (worldwide) -> EN+webtoon.
    Worldwide fallback catches globally-searched IP (e.g. Solo Leveling) whose
    Korean-only interest is thin.
    """
    py = pytrends or _client()
    if py is None:
        return None
    attempts = []
    if override:
        attempts.append((override, "KR"))
    if kr:
        attempts.append((kr, "KR"))
    if en:
        attempts.append((en, ""))          # worldwide
        attempts.append((en + " webtoon", ""))
    for kw, geo in attempts:
        r = _query_one(py, kw, geo)
        if r:
            return r
    return None
