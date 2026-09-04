from ...models.diagram import Diagram
from ...models.label import Label
from ...models.validation import ValidationResult, ValidationLevel
from .base import Validator
from .geometry import FeatureSizeValidator, BoundsValidator, DensityValidator
from .labels import LabelCollisionValidator, LabelSpacingValidator

def get_default_validators() -> list[Validator]:
    return [
        FeatureSizeValidator(),
        BoundsValidator(),
        DensityValidator(),
        LabelCollisionValidator(),
        LabelSpacingValidator()
    ]

def run_validation(
    diagram: Diagram,
    labels: list[Label],
    validators: list[Validator] | None = None
) -> ValidationResult:
    """
    Run all tactile design validators against a diagram and its labels.
    """
    if validators is None:
        validators = get_default_validators()
        
    result = ValidationResult()
    
    for validator in validators:
        messages = validator.validate(diagram, labels)
        for msg in messages:
            if msg.level == ValidationLevel.ERROR:
                result.errors.append(msg)
            elif msg.level == ValidationLevel.WARNING:
                result.warnings.append(msg)
            else:
                result.suggestions.append(msg)
                
    return result
