from abc import ABC, abstractmethod
from ...models.label import BrailleRepresentation


class BrailleTranslator(ABC):
    """
    Abstract interface for Braille translation engines.

    Implementations may use liblouis, a lookup table, or any other backend.
    The interface is kept intentionally simple so that additional grades and
    languages can be added by swapping or composing translators.
    """

    @abstractmethod
    def translate(self, text: str, language: str = "en", grade: int = 1) -> BrailleRepresentation:
        """
        Translate *text* into Braille.

        Args:
            text:     The plain-text string to translate.
            language: ISO-639-1 language code (default ``"en"``).
            grade:    Braille grade (1 = uncontracted, 2 = contracted).

        Returns:
            A ``BrailleRepresentation`` containing Unicode Braille characters,
            dot notation, and metadata.
        """
        ...
