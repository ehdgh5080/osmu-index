"""Format-fit scoring via Claude — synopsis only, no genre label (non-circular).

Returns [drama, film, anime] each 0-100. This is the same premise-based scoring
the index was validated on (18/20 routing). Fully automatable.
"""
import json
import os
import re
from .config import CLAUDE_MODEL

try:
    import anthropic
except Exception:
    anthropic = None

PROMPT = """You are scoring how well a story premise fits three screen-adaptation formats.
You are given ONLY a plot synopsis — NO genre label. Judge from the premise alone.

Rate 0-100 how well this premise would work as each format, considering pacing,
spectacle needs, audience, and production realities:
- drama: live-action episodic series
- film: theatrical feature
- anime: animated series

Synopsis:
\"\"\"{synopsis}\"\"\"

Respond with ONLY a JSON object, no prose:
{{"drama": <int>, "film": <int>, "anime": <int>}}"""


def score_fit(synopsis: str) -> list[int] | None:
    """Return [drama, film, anime] or None on failure."""
    if anthropic is None or not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": PROMPT.format(synopsis=synopsis.strip())}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        text = re.sub(r"```json|```", "", text).strip()
        d = json.loads(text)
        return [int(d["drama"]), int(d["film"]), int(d["anime"])]
    except Exception:
        return None
