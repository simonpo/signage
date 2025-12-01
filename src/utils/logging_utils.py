"""
Logging utilities for the signage system.
Provides structured logging configuration and timing decorators.
"""

import functools
import logging
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.config import Config


def setup_logging(level: str | None = None, log_file: str | None = None) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               If None, uses Config.LOG_LEVEL
        log_file: Path to log file. If None, uses Config.LOG_FILE
    """
    # Determine log level
    if level is None:
        level = Config.LOG_LEVEL

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Determine log file
    if log_file is None:
        log_file = Config.LOG_FILE

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)8s] %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler (simple format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)

    # File handler (detailed format)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)

        root_logger.info(f"Logging to file: {log_path}")

    # Reduce noise from third-party libraries
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    root_logger.info(f"Logging configured at {level.upper()} level")


def timeit(func: Callable | None = None, *, log_args: bool = False) -> Callable:
    """
    Decorator to measure and log function execution time.

    Args:
        func: Function to decorate (provided automatically by @timeit)
        log_args: Whether to log function arguments

    Usage:
        @timeit
        def my_function():
            pass

        @timeit(log_args=True)
        def my_other_function(arg1, arg2):
            pass

    Returns:
        Decorated function
    """

    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = logging.getLogger(f.__module__)

            # Build log message
            func_name = f.__qualname__
            if log_args:
                args_repr = [repr(a) for a in args]
                kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
                signature = ", ".join(args_repr + kwargs_repr)
                msg_start = f"{func_name}({signature})"
            else:
                msg_start = f"{func_name}()"

            logger.debug(f"Starting {msg_start}")

            # Execute function with timing
            start_time = time.perf_counter()
            try:
                result = f(*args, **kwargs)
                elapsed = time.perf_counter() - start_time

                # Log completion with timing
                if elapsed < 0.001:
                    logger.debug(f"Completed {func_name} in {elapsed*1000:.2f}µs")
                elif elapsed < 1.0:
                    logger.debug(f"Completed {func_name} in {elapsed*1000:.1f}ms")
                else:
                    logger.info(f"Completed {func_name} in {elapsed:.2f}s")

                return result

            except Exception as e:
                elapsed = time.perf_counter() - start_time
                logger.error(f"Failed {func_name} after {elapsed:.2f}s: {e}", exc_info=True)
                raise

        return wrapper

    # Handle both @timeit and @timeit() syntax
    if func is None:
        return decorator
    else:
        return decorator(func)


def log_section(title: str, logger: logging.Logger | None = None) -> None:
    """
    Log a section header for better readability.

    Args:
        title: Section title
        logger: Logger to use (defaults to root logger)
    """
    if logger is None:
        logger = logging.getLogger()

    separator = "=" * 60
    logger.info(separator)
    logger.info(f"  {title}")
    logger.info(separator)


class LogContext:
    """
    Context manager for logging blocks of code with timing.

    Usage:
        with LogContext("Processing images"):
            # ... code ...
    """

    def __init__(
        self, description: str, logger: logging.Logger | None = None, level: int = logging.INFO
    ):
        """
        Initialize log context.

        Args:
            description: Description of the operation
            logger: Logger to use (defaults to root logger)
            level: Log level for messages
        """
        self.description = description
        self.logger = logger or logging.getLogger()
        self.level = level
        self.start_time: float | None = None

    def __enter__(self) -> "LogContext":
        """Start timing and log entry."""
        self.start_time = time.perf_counter()
        self.logger.log(self.level, f"Starting: {self.description}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Log completion with timing."""
        if self.start_time is None:
            return
        elapsed = time.perf_counter() - self.start_time

        if exc_type is None:
            if elapsed < 1.0:
                self.logger.log(self.level, f"Completed: {self.description} ({elapsed*1000:.1f}ms)")
            else:
                self.logger.log(self.level, f"Completed: {self.description} ({elapsed:.2f}s)")
        else:
            self.logger.error(
                f"Failed: {self.description} after {elapsed:.2f}s",
                exc_info=(exc_type, exc_val, exc_tb),
            )
