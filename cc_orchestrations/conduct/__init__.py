"""Conduct orchestration workflow.

This module provides the full orchestration workflow for complex features:
1. Parse spec
2. Impact analysis (with voting if high impact)
3. Component loop: skeleton -> implement -> validate -> fix
4. Integration validation
5. Final validation (scaled by risk)
6. Production readiness gate
"""

from .config import CONDUCT_CONFIG, create_default_config
from .workflow import CONDUCT_HANDLERS, create_conduct_workflow

__all__ = [
    'CONDUCT_CONFIG',
    'CONDUCT_HANDLERS',
    'create_conduct_workflow',
    'create_default_config',
]
