"""Simple debug logging for CogitareLink."""

from __future__ import annotations

import logging
from typing import Dict


# Global logger registry
_loggers: Dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger for the given component."""
    if name not in _loggers:
        logger = logging.getLogger(f"cogitarelink.{name}")
        logger.setLevel(logging.INFO)
        
        # Add console handler if none exists
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        _loggers[name] = logger
    
    return _loggers[name]


def set_log_level(level: str = "INFO") -> None:
    """Set global log level for all CogitareLink components."""
    log_level = getattr(logging, level.upper())
    for logger in _loggers.values():
        logger.setLevel(log_level)
        

def disable_logging() -> None:
    """Disable all CogitareLink logging."""
    for logger in _loggers.values():
        logger.disabled = True


def enable_logging() -> None:
    """Re-enable all CogitareLink logging."""
    for logger in _loggers.values():
        logger.disabled = False