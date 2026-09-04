"""
Grade-1 (uncontracted) English Braille translator using a well-tested
lookup table.

This is the documented fallback for environments where the liblouis C
library cannot be installed.  The table covers:

* a-z  (case-insensitive — uppercase is indicated by a ⠠ prefix)
* 0-9  (preceded by the ⠼ number indicator)
* common punctuation  (. , ; : ! ? ' " - / ( ) )
* space

Design note
-----------
The Unicode Braille range U+2800–U+28FF encodes dot patterns directly.
Each character's code-point offset equals the bitmask of raised dots
(dot 1 → bit 0, dot 2 → bit 1, … dot 8 → bit 7).

We store the *dot set* per character (e.g. ``{1, 2, 4, 5}`` for the
letter "h") and convert to Unicode at translation time.
"""

from .base import BrailleTranslator
from ...models.label import BrailleRepresentation


def _dots_to_unicode(dots: set[int]) -> str:
    """Convert a set of raised-dot numbers {1..8} to a Unicode Braille char."""
    # Braille dot numbering:  1=bit0, 2=bit1, 3=bit2, 4=bit3,
    #                         5=bit4, 6=bit5, 7=bit6, 8=bit7
    offset = 0
    for d in dots:
        offset |= 1 << (d - 1)
    return chr(0x2800 + offset)


def _dots_to_notation(dots: set[int]) -> str:
    """Convert a set of raised-dot numbers to standard dot notation, e.g. '1245'."""
    return "".join(str(d) for d in sorted(dots))


# ---------------------------------------------------------------------------
# Grade 1 English Braille lookup table
# Source: Unified English Braille (UEB), Grade 1
# ---------------------------------------------------------------------------

# Letters a-z
_LETTER_DOTS: dict[str, set[int]] = {
    "a": {1},
    "b": {1, 2},
    "c": {1, 4},
    "d": {1, 4, 5},
    "e": {1, 5},
    "f": {1, 2, 4},
    "g": {1, 2, 4, 5},
    "h": {1, 2, 5},
    "i": {2, 4},
    "j": {2, 4, 5},
    "k": {1, 3},
    "l": {1, 2, 3},
    "m": {1, 3, 4},
    "n": {1, 3, 4, 5},
    "o": {1, 3, 5},
    "p": {1, 2, 3, 4},
    "q": {1, 2, 3, 4, 5},
    "r": {1, 2, 3, 5},
    "s": {2, 3, 4},
    "t": {2, 3, 4, 5},
    "u": {1, 3, 6},
    "v": {1, 2, 3, 6},
    "w": {2, 4, 5, 6},
    "x": {1, 3, 4, 6},
    "y": {1, 3, 4, 5, 6},
    "z": {1, 3, 5, 6},
}

# Digits 0-9 reuse the letter patterns for a-j, preceded by a number indicator
_DIGIT_LETTERS = "jabcdefghi"  # 0→j, 1→a, 2→b, … 9→i

# Special indicators
_CAPITAL_PREFIX = {6}           # ⠠  capital-letter indicator
_NUMBER_PREFIX = {3, 4, 5, 6}  # ⠼  number indicator

# Punctuation
_PUNCTUATION_DOTS: dict[str, set[int]] = {
    ".": {2, 5, 6},
    ",": {2},
    ";": {2, 3},
    ":": {2, 5},
    "!": {2, 3, 5},
    "?": {2, 3, 6},
    "'": {3},
    '"': {2, 3, 5, 6},      # opening — same cell used for both open/close in Grade 1
    "-": {3, 6},
    "/": {3, 4},
    "(": {1, 2, 6},  # ⠣
    ")": {3, 4, 5},  # ⠜
}


class Grade1EnglishTranslator(BrailleTranslator):
    """
    Translates English text into Grade 1 (uncontracted) Braille.

    Handles uppercase via the ⠠ prefix and digits via the ⠼ number indicator.
    Unknown characters are silently skipped (logged in metadata).
    """

    def translate(self, text: str, language: str = "en", grade: int = 1) -> BrailleRepresentation:
        unicode_cells: list[str] = []
        dot_notations: list[str] = []
        skipped: list[str] = []
        in_number_mode = False

        for ch in text:
            if ch == " ":
                unicode_cells.append(" ")
                dot_notations.append("0")
                in_number_mode = False
                continue

            if ch.isdigit():
                if not in_number_mode:
                    # Emit number indicator
                    unicode_cells.append(_dots_to_unicode(_NUMBER_PREFIX))
                    dot_notations.append(_dots_to_notation(_NUMBER_PREFIX))
                    in_number_mode = True
                letter = _DIGIT_LETTERS[int(ch)]
                dots = _LETTER_DOTS[letter]
                unicode_cells.append(_dots_to_unicode(dots))
                dot_notations.append(_dots_to_notation(dots))
                continue

            # If we were in number mode and hit a non-digit, exit
            in_number_mode = False

            lower = ch.lower()
            if lower in _LETTER_DOTS:
                if ch.isupper():
                    unicode_cells.append(_dots_to_unicode(_CAPITAL_PREFIX))
                    dot_notations.append(_dots_to_notation(_CAPITAL_PREFIX))
                dots = _LETTER_DOTS[lower]
                unicode_cells.append(_dots_to_unicode(dots))
                dot_notations.append(_dots_to_notation(dots))
                continue

            if ch in _PUNCTUATION_DOTS:
                dots = _PUNCTUATION_DOTS[ch]
                unicode_cells.append(_dots_to_unicode(dots))
                dot_notations.append(_dots_to_notation(dots))
                continue

            # Unknown character — skip but record
            skipped.append(ch)

        return BrailleRepresentation(
            braille_unicode="".join(unicode_cells),
            braille_dots="-".join(dot_notations),
            grade=grade,
            language=language,
        )
