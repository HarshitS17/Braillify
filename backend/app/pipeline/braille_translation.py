"""
Convenience function for translating labels on a Diagram.
Keeps Braille generation separate from rendering (as required by spec).
"""

from ..models.label import Label
from .braille.base import BrailleTranslator
from .braille.grade1_english import Grade1EnglishTranslator


def translate_labels(
    labels: list[Label],
    translator: BrailleTranslator | None = None,
    language: str = "en",
    grade: int = 1,
) -> list[Label]:
    """
    Populate the ``braille`` field on each label using the given translator.

    Args:
        labels:     The labels to translate.
        translator: An optional translator instance (defaults to Grade1EnglishTranslator).
        language:   ISO language code.
        grade:      Braille grade.

    Returns:
        The same list of labels, with ``braille`` fields populated in-place.
    """
    if translator is None:
        translator = Grade1EnglishTranslator()

    for label in labels:
        if label.text:
            label.braille = translator.translate(label.text, language=language, grade=grade)

    return labels
