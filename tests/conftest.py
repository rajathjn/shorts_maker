import logging
from pathlib import Path

import pytest
import yaml

from ShortsMaker import ShortsMaker


@pytest.fixture
def setup_file():
    """
    Fixture to provide the setup file path.

    Returns:
        pathlib.Path: Path to the setup configuration file.
    """
    return Path(r"C:\Users\rajath\Downloads\Personal Projects\youtube_shorts_automation\setup.yml")


@pytest.fixture
def setup_file_cfg(setup_file):
    """
    Fixture to load and provide the setup configuration file content.

    Args:
        setup_file (pathlib.Path): Path to the setup file.

    Returns:
        dict: Parsed YAML content of the setup file.
    """
    with open(setup_file) as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    return cfg


@pytest.fixture
def shorts_maker(setup_file):
    """
    Fixture to provide an instance of ShortsMaker.

    Args:
        setup_file (pathlib.Path): Path to the setup file.

    Returns:
        ShortsMaker: An instance of the ShortsMaker class.
    """
    return ShortsMaker(setup_file)


@pytest.fixture
def mock_logger():
    """
    Fixture to provide a mock logger for testing.

    Returns:
        logging.Logger: A mocked logger instance.
    """
    return logging.getLogger("test_logger")
