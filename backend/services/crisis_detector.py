"""Crisis detection — keyword pre-screening + AI assessment"""
import re

# Crisis keywords in Russian and English
CRISIS_KEYWORDS_RU = [
    r"убить\s*себя",
    r"покончить\s*с\s*собой",
    r"суицид",
    r"хочу\s*умереть",
    r"не\s*хочу\s*жить",
    r"лучше\s*бы\s*меня\s*не\s*было",
    r"нет\s*смысла\s*жить",
    r"повеситься",
    r"прыгну",
    r"резать\s*(себя|вены)",
    r"самоубийств",
    r"конец\s*всему",
]

CRISIS_KEYWORDS_EN = [
    r"kill\s*myself",
    r"want\s*to\s*die",
    r"suicide",
    r"end\s*it\s*all",
    r"no\s*reason\s*to\s*live",
    r"self[- ]?harm",
    r"better\s*off\s*dead",
]

ALL_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in CRISIS_KEYWORDS_RU + CRISIS_KEYWORDS_EN
]

CRISIS_RESPONSE = """Я слышу, что тебе сейчас очень тяжело. Твоя боль реальна, и я благодарю тебя за честность.

Я — AI-инструмент, и у меня нет возможности оказать тебе помощь, которая нужна в этот момент. Пожалуйста, обратись к людям, которые могут помочь:

**Горячая линия психологической помощи (Россия):**
8-800-2000-122 (бесплатно, 24/7)

**Телефон доверия:**
8-495-988-44-34

Ты не один. Пожалуйста, позвони прямо сейчас. Живой человек выслушает и поможет.

Я буду здесь, когда ты будешь готов продолжить. Но сейчас самое важное — поговорить с человеком."""


def check_crisis(text: str) -> bool:
    """Check if user message contains crisis indicators.

    Returns True if crisis keywords are detected.
    This is a fast pre-screen before AI assessment.
    """
    for pattern in ALL_PATTERNS:
        if pattern.search(text):
            return True
    return False


def get_crisis_response() -> str:
    """Return the standard crisis response message."""
    return CRISIS_RESPONSE
