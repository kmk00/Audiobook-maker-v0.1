import re
from typing import Optional, Tuple

# Inline voice-direction markup, e.g. "<<slow, angry>>" or "<<cfg:5 speak calmly>>".
DIRECTION_RE = re.compile(r"<<(.*?)>>", re.DOTALL)
CFG_RE = re.compile(r"(?:^|\s)cfg\s*:\s*([0-9]+(?:\.[0-9]+)?)\b", re.IGNORECASE)


def extract_direction(text: str) -> Tuple[str, Optional[str], Optional[float]]:
    """Strip `<<...>>` direction tags from the text.

    Returns (clean_text, direction_instruction, cfg_scale_override).
    A `cfg:N` shorthand inside a tag sets the CFG-scale override instead of
    being part of the instruction.
    """
    direction = None
    cfg_override = None

    def _handle(match: re.Match) -> str:
        nonlocal direction, cfg_override
        content = match.group(1).strip()
        if not content:
            return ""
        cfg_match = CFG_RE.search(content)
        if cfg_match:
            cfg_override = float(cfg_match.group(1))
            content = CFG_RE.sub(" ", content).strip()
        if content and direction is None:
            direction = content
        elif content:
            direction = f"{direction}; {content}"
        return " "

    clean = DIRECTION_RE.sub(_handle, text)
    clean = re.sub(r"[ \t]+", " ", clean)
    clean = re.sub(r" ([.,!?])", r"\1", clean)
    return clean.strip(), direction, cfg_override
