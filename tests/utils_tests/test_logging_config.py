import logging
from unittest.mock import patch

import pytest

import ShortsMaker
import ShortsMaker.utils
from ShortsMaker.utils.logging_config import (
    LOGGERS,
    configure_logging,
    get_logger,
)


@pytest.fixture
def reset_logging_state():
    """Reset global logging state between tests"""
    global INITIALIZED, LOGGERS
    INITIALIZED = False
    LOGGERS.clear()
    yield
    INITIALIZED = False
    LOGGERS.clear()


def test_get_logger_creates_new_logger(reset_logging_state):
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"
    assert len(logger.handlers) == 2
    assert not logger.propagate


def test_get_logger_returns_cached_logger(reset_logging_state):
    logger1 = get_logger("test_logger")
    logger2 = get_logger("test_logger")
    assert logger1 is logger2


def test_configure_logging_updates_settings(reset_logging_state, tmp_path):
    test_log_file = tmp_path / "test.log"
    test_level = "INFO"
    configure_logging(log_file=test_log_file, level=test_level, enable=True)
    assert ShortsMaker.utils.logging_config.LOG_FILE == test_log_file
    assert ShortsMaker.utils.logging_config.LOG_LEVEL == test_level
    assert ShortsMaker.utils.logging_config.LOGGING_ENABLED is True
    assert ShortsMaker.utils.logging_config.INITIALIZED is True


def test_configure_logging_updates_existing_loggers(reset_logging_state):
    logger = get_logger("test_logger")

    configure_logging(level="INFO", enable=True)
    assert logger.level == logging.INFO

    configure_logging(enable=False)
    assert logger.level == logging.CRITICAL


@patch("pathlib.Path.mkdir")
def test_configure_logging_creates_directory(mock_mkdir):
    configure_logging()
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_disabled_logging_sets_critical_level(reset_logging_state):
    configure_logging(enable=False)
    logger = get_logger("test_logger")
    assert logger.level == logging.CRITICAL
