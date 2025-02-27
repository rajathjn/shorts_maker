import logging
from pathlib import Path

import pytest
import yaml

from ShortsMaker import ShortsMaker


@pytest.fixture
def setup_file():
    return Path(__file__).parent.parent / "setup.yml"


@pytest.fixture
def setup_file_cfg(setup_file):
    with open(setup_file) as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    return cfg


@pytest.fixture
def shorts_maker(setup_file):
    return ShortsMaker(setup_file)


@pytest.fixture
def mock_logger():
    return logging.getLogger("test_logger")
