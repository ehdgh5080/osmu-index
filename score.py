"""Turn raw signals into the model's numbers — identical formulas to the site."""
import math
from statistics import median
from .config import SRC_WEIGHTS, FMT_WEIGHTS, FMT_WSUM, VIABLE_FIT


def optionality(fit) -> int:
    d, f, a = fit
    return round((d / 100 * FMT_WEIGHTS["drama"] + f / 100 * FMT_WEIGHTS["film"]
                  + a / 100 * FMT_WEIGHTS["anime"]) / FMT_WSUM * 100)


def source_strength(comp) -> int:
    r, e, s, m = comp
    return round(SRC_WEIGHTS["reach"] * r + SRC_WEIGHTS["eng"] * e
                 + SRC_WEIGHTS["scale"] * s + SRC_WEIGHTS["mom"] * m)


def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


# ---- component derivation from raw signals ----
def scale_score(chapters: int) -> int:
    """More chapters = deeper world/investment. Log-shaped, saturates."""
    if not chapters:
        return 50
    return int(clamp(30 + 40 * math.log10(max(chapters, 10) / 30)))


def momentum_score(slope: float | None) -> int:
    """slope = recent interest / prior interest. 1.0 -> steady (~60)."""
    if slope is None:
        return 60
    if slope >= 1.4:
        return 92
    if slope >= 1.15:
        return 80
    if slope >= 0.9:
        return 65
    if slope >= 0.7:
        return 50
    return 38  # clearly declining (e.g. past-peak like Mount Hua)


def reach_score(peak: float | None, peaks_pool: list[float]) -> int:
    """Percentile of Trends peak within the current pool — self-calibrating."""
    if peak is None or not peaks_pool:
        return 60
    below = sum(1 for x in peaks_pool if x < peak)
    return int(clamp(35 + 60 * below / max(1, len(peaks_pool) - 1)))


def eng_score(rating_0_10: float | None, recent: float | None, recents_pool: list[float]) -> int:
    """Prefer a public rating (x10). Else use sustained interest percentile."""
    if rating_0_10:
        return int(clamp(rating_0_10 * 10))
    if recent is not None and recents_pool:
        below = sum(1 for x in recents_pool if x < recent)
        return int(clamp(40 + 50 * below / max(1, len(recents_pool) - 1)))
    return 60


def quadrant(src: int, opt: int, src_t: float, opt_t: float) -> str:
    hs, ho = src >= src_t, opt >= opt_t
    return ("FRANCHISE" if hs and ho else "TENTPOLE" if hs
            else "NICHE" if ho else "PASS")


def thresholds(items) -> tuple[float, float]:
    return median([i["src"] for i in items]), median([i["o"] for i in items])
