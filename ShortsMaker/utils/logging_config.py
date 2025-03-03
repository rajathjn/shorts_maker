import logging
import os
from pathlib import Path

from colorlog import ColoredFormatter

# prevent huggingface symlink warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "true"

# Global configuration
LOG_FILE: Path | str = "ShortsMaker.log"
LOG_LEVEL: str = "DEBUG"
LOGGING_ENABLED: bool = True
INITIALIZED: bool = False

# Cache of configured loggers
LOGGERS: dict[str, logging.Logger] = {}


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger with the specified name, typically __name__ from the module.
    If the logging system has not been initialized, it will use default settings.

    Args:
        name (str): The logger name, typically passed as __name__ from the module.
            This ensures proper hierarchical naming of loggers.

    Returns:
        logging.Logger: A configured logger instance.
    """
    global LOG_FILE, LOG_LEVEL, LOGGING_ENABLED, INITIALIZED, LOGGERS

    # Initialize logging system with defaults if not already done
    if not INITIALIZED:
        configure_logging()

    # Return existing logger if already configured
    if name in LOGGERS:
        return LOGGERS[name]

    # Create a new logger
    logger = logging.getLogger(name)

    # Don't add handlers if this is a child logger
    # Parent loggers will handle it through hierarchy
    if not logger.handlers:
        # Create Console
        console_handler = logging.StreamHandler()
        color_formatter = ColoredFormatter(
            "{log_color}{asctime} - {name} - {funcName} - {levelname} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
            reset=True,
        )
        console_handler.setFormatter(color_formatter)

        # Create File Handler
        file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
        formatter = logging.Formatter(
            "{asctime} - {name} - {funcName} - {levelname} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        # Set logging level based on enable flag
        if LOGGING_ENABLED:
            logger.setLevel(LOG_LEVEL)
        else:
            logger.setLevel(logging.CRITICAL)

        # Prevent propagation to avoid duplicate logs
        logger.propagate = False

    # Store the configured logger
    LOGGERS[name] = logger

    return logger


def configure_logging(
    log_file: Path | str = LOG_FILE, level: str | int = LOG_LEVEL, enable: bool = LOGGING_ENABLED
) -> None:
    """
    Configure the global logging settings.
    This function can be called by users to customize logging behavior.

    Args:
        log_file (str | Path): Path to the log file.
        level (str | int): Logging level ('DEBUG', 'INFO', etc.).
        enable (bool): Whether to enable logging.
    """
    global LOG_FILE, LOG_LEVEL, LOGGING_ENABLED, INITIALIZED, LOGGERS

    # Update configuration with provided values
    LOG_FILE = Path(log_file) if isinstance(log_file, str) else log_file
    LOG_LEVEL = level
    LOGGING_ENABLED = enable

    # Create log directory if it doesn't exist
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Update all existing loggers with new settings
    for logger_name, logger in LOGGERS.items():
        # Update log level
        if LOGGING_ENABLED:
            logger.setLevel(LOG_LEVEL)
        else:
            logger.setLevel(logging.CRITICAL)

    INITIALIZED = True
