"""
Logging utilities for the manipulation detection toolkit.

Provides centralized logging configuration with consistent formatting.
"""

import logging
import sys
from typing import Optional


def get_logger(
    name: str,
    level: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__ of the calling module).
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, defaults to INFO.
        format_string: Custom format string. If None, uses default format.
        
    Returns:
        logging.Logger: Configured logger instance.
        
    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
        2025-11-14 10:30:45 - module_name - INFO - Processing started
        
        >>> logger = get_logger(__name__, level='DEBUG')
        >>> logger.debug("Debug information")
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Set level
    if level is None:
        level = 'INFO'
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        
        # Create formatter
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        formatter = logging.Formatter(
            format_string,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    return logger


def setup_root_logger(level: str = 'INFO') -> None:
    """
    Set up the root logger for the entire application.
    
    This is useful for setting a global logging level.
    
    Args:
        level: Logging level for the root logger.
        
    Examples:
        >>> setup_root_logger('DEBUG')
        >>> # Now all loggers will default to DEBUG level
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )


def log_function_call(logger: logging.Logger):
    """
    Decorator to log function calls (for debugging).
    
    Args:
        logger: Logger instance to use.
        
    Returns:
        Decorator function.
        
    Examples:
        >>> logger = get_logger(__name__)
        >>> @log_function_call(logger)
        ... def my_function(x, y):
        ...     return x + y
        >>> result = my_function(1, 2)
        # Logs: "Calling my_function with args=(1, 2), kwargs={}"
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(
                f"Calling {func.__name__} with args={args}, kwargs={kwargs}"
            )
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned {result}")
            return result
        return wrapper
    return decorator


if __name__ == "__main__":
    # Demo usage
    logger = get_logger(__name__, level='DEBUG')
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Demo with decorator
    @log_function_call(logger)
    def add(a: int, b: int) -> int:
        return a + b
    
    result = add(5, 3)
    logger.info(f"Result: {result}")

