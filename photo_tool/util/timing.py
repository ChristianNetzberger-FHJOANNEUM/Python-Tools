"""
Timing utilities for performance measurement
"""

import time
from contextlib import contextmanager
from typing import Generator

from .logging import get_logger


logger = get_logger("timing")


@contextmanager
def timer(label: str, log_level: str = "INFO") -> Generator[None, None, None]:
    """
    Context manager for timing code blocks
    
    Usage:
        with timer("Processing photos"):
            # ... code ...
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        msg = f"{label}: {elapsed:.2f}s"
        
        if log_level == "DEBUG":
            logger.debug(msg)
        elif log_level == "INFO":
            logger.info(msg)
        elif log_level == "WARNING":
            logger.warning(msg)


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
