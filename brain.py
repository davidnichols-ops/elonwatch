"""
brain.py - ElonWatch Intelligence Engine
Classifies, scores, and extracts meaning from raw scraped items.
No LLM needed — pure rule-based signal extraction that runs instantly.

Output per item:
  domain      : SPACE | AI | POLITICS | MONEY | TECH | CULTURE | EGO | CHAOS
  signal_type : DIRECTIVE | VISION | REACTION | HUMOR | SIGNAL | NOISE
  urgency     : 0-10 (10 = drop-everything important)
  sentiment   : BULLISH | BEARISH | NEUTRAL | HOSTILE | PLAYFUL
  tags        : list of matched keyword tags
  summary     : one-line synthesized meaning (rule-based template)
"""

import re
from dataclasses import dataclass, field

# ── Domain taxonomy ────────────────────────────────────────────────────────────
DOMAIN_KEYWORDS = {
    "SPACE": [
        "spacex", "starship", "falcon", "rocket", "mars", "orbit", "launch",
        "iss", "astronaut", "nasa", "satellite", "booster", "raptor", "starlink",
        "landing", "reentry", "payload", "lunar", "moon", "launch pad",
    ],
    "AI": [
        "xai", "grok", "ai", "artificial intelligence", "llm", "model",
        "neural", "machine learning", "chatgpt", "openai", "training",
        "agi", "superintelligence", "data", "compute", "inference",
        "alignment", "safety", "benchmark", "colossus",
    ],
    "POLITICS": [
        "doge", "government", "biden", "trump", "congress", "senate",
        "democrat", "republican", "election", "vote", "president",
        "white house", "policy", "budget", "federal", "regulation",
        "spending", "department", "secretary", "immigration", "border",
        "lawsuit", "court", "legal", "free speech", "censorship",
        "woke", "dei", "bureaucrat", "swamp",
    ],
    "MONEY": [
        "tesla", "stock", "shares", "billion", "million", "revenue",
        "earnings", "profit", "valuation", "ipo", "dogecoin", "doge",
        "bitcoin", "crypto", "market", "investor", "fund", "capital",
        "finance", "economy", "interest rate", "inflation", "bank",
        "acquisition", "deal", "merger", "price target",
    ],
    "TECH": [
        "software", "engineering", "code", "app", "update", "feature",
        "product", "design", "autopilot", "fsd", "neuralink", "chip",
        "hardware", "battery", "energy", "solar", "grid", "powerwall",
        "boring company", "tunnel", "hyperloop", "twitter", "x.com",
        "algorithm", "platform", "api",
    ],
    "CULTURE": [
        "meme", "tweet", "post", "interview", "podcast", "video",
        "book", "science", "philosophy", "simulation", "consciousness",
        "comedy", "joke", "funny", "trolling", "shitpost", "reply",
        "human", "civilization", "future", "kids", "family",
    ],
    "EGO": [
        "richest", "ceo", "founder", "elon said", "elon claims",
        "elon wants", "elon believes", "elon warns", "world's",
        "most powerful", "genius", "visionary", "controversial",
        "criticized", "praised", "worshiped", "attacked",
    ],
    "CHAOS": [
        "fired", "resign", "crash", "explosion", "failed", "failure",
        "crisis", "emergency", "warning", "danger", "threat",
        "ban", "block", "suspended", "deleted", "outrage", "scandal",
        "controversy", "backlash", "meltdown", "breaking",
    ],
    "GLAZE": [
        "genius", "visionary", "brilliant", "incredible", "amazing", "greatest",
        "legendary", "icon", "hero", "pioneer", "revolutionary", "goat",
        "inspires", "inspiring", "admire", "praise", "praises", "praised",
        "thank elon", "love elon", "grateful", "thank you elon", "saved",
        "changed my life", "changed the world", "only elon", "elon is right",
        "elon deserves", "respect elon", "support elon", "proud of elon",
        "well done elon", "remarkable", "outstanding", "historic achievement",
        "congrat", "elon wins", "elon nailed",
    ],
}

# ── Signal type patterns ───────────────────────────────────────────────────────
DIRECTIVE_PATTERNS = [
    r"\b(will|going to|plan(s|ning)?|intend|commit|announce[ds]?|launch(ing|es)?)\b",
    r"\b(build(ing)?|create|deploy|release|ship|acquire|partner)\b",
    r"\b(order(ed|s)?|mandate|require|must|should|need to)\b",
    r"\b(demand(s|ed)?|insist|urge[ds]?)\b",
]

VISION_PATTERNS = [
    r"\b(goal|vision|mission|future|predict|believe[ds]?|think[s]?)\b",
    r"\b(humanity|civilization|multiplanet|species|long.?term|decades?)\b",
    r"\b(ultimate(ly)?|eventually|someday|inevitable)\b",
]

HUMOR_PATTERNS = [
    r"\b(lol|lmao|haha|420|69|kek|based|cringe|cope|seethe)\b",
    r"[😂🤣😹💀🫡🤌]",
    r"\b(meme|trolling?|shitpost|savage|ratio)\b",
]

REACTION_PATTERNS = [
    r"\b(respond(s|ed)?|reply|replies|react(s|ed)?|counter|fire[ds]? back)\b",
    r"\b(wrong|false|fake|lie|disagree|disputed?|refute)\b",
]

# ── Urgency signals ────────────────────────────────────────────────────────────
URGENCY_BOOSTERS = {
    10: ["breaking", "just announced", "emergency", "explosion", "crashed",
         "war", "launch today", "now live", "happening now"],
    8:  ["announces", "officially", "confirmed", "just said", "new", "exclusive",
         "starship", "test flight", "ipo", "acquisition"],
    6:  ["says", "claims", "warns", "predicts", "plans to", "will"],
    4:  ["reportedly", "sources say", "rumored", "possibly", "might"],
    2:  ["opinion", "analysis", "review", "recap", "thread"],
}

# ── Sentiment keywords ─────────────────────────────────────────────────────────
SENTIMENT_MAP = {
    "BULLISH":  ["success", "record", "profit", "milestone", "breakthrough",
                 "amazing", "incredible", "win", "launch", "approved", "growth"],
    "BEARISH":  ["fail", "loss", "decline", "crash", "drop", "layoff",
                 "problem", "delay", "miss", "cut", "debt"],
    "HOSTILE":  ["attack", "sue", "ban", "fired", "war", "threaten",
                 "destroy", "fight", "enemy", "hate", "wrong"],
    "PLAYFUL":  ["lol", "joke", "meme", "funny", "troll", "haha", "420", "69"],
}

# ── Domain-specific summary templates ─────────────────────────────────────────
SUMMARY_TEMPLATES = {
    ("SPACE", "DIRECTIVE"):   "MISSION UPDATE: {title}",
    ("SPACE", "VISION"):      "CIVILIZATIONAL GOAL: {title}",
    ("AI", "DIRECTIVE"):      "AI DEPLOYMENT: {title}",
    ("AI", "VISION"):         "MACHINE MIND THEORY: {title}",
    ("POLITICS", "DIRECTIVE"):"POWER MOVE: {title}",
    ("POLITICS", "REACTION"): "COUNTER-SIGNAL: {title}",
    ("MONEY", "SIGNAL"):      "CAPITAL FLOW: {title}",
    ("MONEY", "DIRECTIVE"):   "MARKET DIRECTIVE: {title}",
    ("CHAOS", "SIGNAL"):      "!! ALERT: {title}",
    ("CHAOS", "DIRECTIVE"):   "!! DIRECTIVE: {title}",
    ("EGO", "REACTION"):      "STATUS RESPONSE: {title}",
    ("CULTURE", "HUMOR"):     "MEME EMISSIONS: {title}",
}

DOMAIN_ICONS = {
    "SPACE":    "🚀",
    "AI":       "🧠",
    "POLITICS": "⚡",
    "MONEY":    "◈",
    "TECH":     "⬡",
    "CULTURE":  "◉",
    "EGO":      "★",
    "CHAOS":    "!!",
    "GLAZE":    "✦",
}

DOMAIN_COLORS = {
    "SPACE":    "bright_cyan",
    "AI":       "bright_magenta",
    "POLITICS": "bright_yellow",
    "MONEY":    "bright_green",
    "TECH":     "cyan",
    "CULTURE":  "white",
    "EGO":      "yellow",
    "CHAOS":    "bright_red",
    "GLAZE":    "bright_yellow",
}

SIGNAL_COLORS = {
    "DIRECTIVE": "bright_white",
    "VISION":    "bright_cyan",
    "REACTION":  "yellow",
    "HUMOR":     "bright_black",
    "SIGNAL":    "bright_green",
    "NOISE":     "bright_black",
}

SENTIMENT_COLORS = {
    "BULLISH":  "bright_green",
    "BEARISH":  "red",
    "HOSTILE":  "bright_red",
    "PLAYFUL":  "magenta",
    "NEUTRAL":  "bright_black",
}


@dataclass
class Scored:
    row_id: int
    title: str
    author: str
    source: str
    url: str
    content: str
    published: str
    scraped_at: str

    domain: str = "CULTURE"
    signal_type: str = "NOISE"
    urgency: int = 1
    sentiment: str = "NEUTRAL"
    tags: list[str] = field(default_factory=list)
    summary: str = ""


def _text(title: str, content: str) -> str:
    """Combined lowercase text for matching."""
    return (title + " " + (content or "")).lower()


def classify_domain(text: str) -> tuple[str, list[str]]:
    """Return best-match domain and matched tags."""
    scores: dict[str, int] = {}
    matched_tags: dict[str, list[str]] = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        hits = [kw for kw in keywords if kw in text]
        if hits:
            scores[domain] = len(hits)
            matched_tags[domain] = hits
    if not scores:
        return "CULTURE", []
    best = max(scores, key=lambda d: scores[d])
    return best, matched_tags[best][:8]


def classify_signal(text: str) -> str:
    for pat in HUMOR_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return "HUMOR"
    for pat in DIRECTIVE_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return "DIRECTIVE"
    for pat in VISION_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return "VISION"
    for pat in REACTION_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return "REACTION"
    return "SIGNAL"


def score_urgency(text: str, domain: str, signal_type: str) -> int:
    urgency = 2
    for score, keywords in URGENCY_BOOSTERS.items():
        for kw in keywords:
            if kw in text:
                urgency = max(urgency, score)
    # Boost for chaos or directive
    if domain == "CHAOS":
        urgency = min(10, urgency + 3)
    if signal_type == "DIRECTIVE":
        urgency = min(10, urgency + 1)
    if signal_type == "HUMOR":
        urgency = max(1, urgency - 3)
    return urgency


def classify_sentiment(text: str) -> str:
    scores = {s: 0 for s in SENTIMENT_MAP}
    for sentiment, keywords in SENTIMENT_MAP.items():
        for kw in keywords:
            if kw in text:
                scores[sentiment] += 1
    best = max(scores, key=lambda s: scores[s])
    if scores[best] == 0:
        return "NEUTRAL"
    return best


def make_summary(title: str, domain: str, signal_type: str) -> str:
    template = SUMMARY_TEMPLATES.get((domain, signal_type))
    if template:
        return template.format(title=title[:90])
    return f"{domain} // {signal_type}: {title[:90]}"


def score_item(row) -> Scored:
    """Take a DB row and return a fully scored Scored object."""
    title = row["title"] or ""
    content = row["content"] or ""
    full_text = _text(title, content)

    domain, tags = classify_domain(full_text)
    signal_type = classify_signal(full_text)
    urgency = score_urgency(full_text, domain, signal_type)
    sentiment = classify_sentiment(full_text)
    summary = make_summary(title, domain, signal_type)

    return Scored(
        row_id=row["id"],
        title=title,
        author=row["author"] or "",
        source=row["source"] or "",
        url=row["url"] or "",
        content=content,
        published=row["published"] or "",
        scraped_at=row["scraped_at"] or "",
        domain=domain,
        signal_type=signal_type,
        urgency=urgency,
        sentiment=sentiment,
        tags=tags,
        summary=summary,
    )


def is_high_signal(s: Scored) -> bool:
    """True if this item is worth a push notification."""
    if s.urgency >= 7:
        return True
    if s.source == "twitter" and s.author == "@elonmusk" and s.urgency >= 4:
        return True
    if s.domain == "CHAOS":
        return True
    return False


def is_elon_tweet(s: Scored) -> bool:
    return s.source == "twitter" and "@elonmusk" in s.author.lower()
