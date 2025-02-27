import logging
import os
from pathlib import Path

from colorlog import ColoredFormatter

# prevent huggingface symlink warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "true"


def setup_package_logging(
    log_file: str | Path,
    logger_name: str = __name__,
    level: str | int = "INFO",
    enable: bool = True,
):
    """
    Sets up customized logging for a package. This function configures a logger with
    console and file handlers, specifies log formatting (including colored output
    for console logs), and applies a logging level based on an `enable` flag. It
    prevents log propagation to the root logger, ensuring the logger operates
    independently while avoiding duplicate logging configurations.

    Args:
        log_file (str | Path): Path to the file where log messages will be saved.
        logger_name (str): Name of the logger. Defaults to the current module's name
            if not provided.
        level (str | int): Logging level (e.g., 'DEBUG', 'INFO', or corresponding
            numeric levels). Defaults to 'INFO'.
        enable (bool): Flag indicating whether logging is enabled. When set to
            False, the logger is configured to only log critical messages.

    Returns:
        logging.Logger: Configured logger instance with the specified settings.
    """
    # Create the root logger for the package
    logger = logging.getLogger(logger_name)

    # Clear any existing handlers to avoid duplicate logs
    logger.handlers.clear()

    # Create handlers

    # Create Console
    console_handler = logging.StreamHandler()
    color_formatter = ColoredFormatter(
        "{log_color}{asctime} - {name} - {levelname} - {message}",
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
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    formatter = logging.Formatter(
        "{asctime} - {name} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Set logging level based on enable flag
    if enable:
        logger.setLevel(level)
    else:
        logger.setLevel(logging.CRITICAL)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger
