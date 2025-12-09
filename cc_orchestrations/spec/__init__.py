"""Spec formalization and validation.

This module provides:
- SpecFormalizer: Converts brainstorm artifacts into validated manifest
- ManifestValidator: Validates manifests against schemas and logic rules
- ValidationError: Specific validation error with suggestions
"""

from .formalizer import FormalizationResult, SpecFormalizer
from .validator import ManifestValidator, ValidationError, ValidationResult

__all__ = [
    'FormalizationResult',
    'ManifestValidator',
    'SpecFormalizer',
    'ValidationError',
    'ValidationResult',
]
