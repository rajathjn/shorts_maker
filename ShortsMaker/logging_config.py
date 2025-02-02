import logging
import os
from pathlib import Path
from typing import Union

from colorlog import ColoredFormatter

# prevent huggingface symlink warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "true"


def setup_package_logging(
    log_file: Union[str, Path],
    logger_name: str = __name__,
    level: Union[str, int] = "INFO",
    enable: bool = True,
):
    """
    Sets up the logging configuration for the given package. This function creates a logger with
    both console and file handlers, applies specified formatting styles, sets the logging level,
    and optionally disables or enables logging based on the given parameters. The root logger
    propagation is disabled to limit log handling to the configured handlers only.

    Args:
        logger_name: The name for the logger
        log_file (str | Path): The file location where logs will be written. If the file does not
            exist, it will be created. Logs are stored in UTF-8 encoding mode.
        level (str | int): The logging level to set for the logger. Common options are "DEBUG",
            "INFO", "WARNING", "ERROR", or "CRITICAL". Defaults to "INFO" if not specified.
        enable (bool): A flag indicating whether logging should be enabled. If set to False,
            logging is effectively disabled by setting the logging level to CRITICAL. Defaults to True.

    Returns:
        logging.Logger: The configured logger for the package.
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
