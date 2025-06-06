"""Vocabulary management for CogitareLink.

Multi-vocabulary JSON-LD context composition with collision detection.
"""

from .registry import registry, VocabEntry, ContextBlock, Versions
from .composer import composer, Composer  
from .collision import resolver, Strategy, Plan

__all__ = [
    'registry', 'VocabEntry', 'ContextBlock', 'Versions',
    'composer', 'Composer',
    'resolver', 'Strategy', 'Plan'
]