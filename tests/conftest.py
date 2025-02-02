from pathlib import Path

import pytest
import yaml

from ShortsMaker import GenerateImage, ShortsMaker


@pytest.fixture
def setup_file():
    return Path(
        r"C:\Users\rajath\Downloads\Personal Projects\youtube_shorts_automation\setup.yml"
    )


@pytest.fixture
def setup_file_cfg(setup_file):
    with open(setup_file, "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    return cfg


@pytest.fixture
def shorts_maker(setup_file):
    return ShortsMaker(setup_file)


@pytest.fixture
def generate_image(setup_file):
    return GenerateImage(setup_file)
