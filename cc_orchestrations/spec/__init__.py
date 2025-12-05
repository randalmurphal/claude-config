"""Spec creation and validation.

This module provides tools for creating and validating specs:
- ManifestValidator: Python validation of manifest.json
- SpecFormalizer: Convert brainstorm artifacts to validated manifest
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
