import logging
from pathlib import Path

import pytest

from ShortsMaker import ShortsMaker


@pytest.fixture
def setup_file():
    return Path(__file__).parent / "data" / "setup.yml"


@pytest.fixture
def shorts_maker(setup_file):
    return ShortsMaker(setup_file)


@pytest.fixture
def mock_logger():
    return logging.getLogger("test_logger")
