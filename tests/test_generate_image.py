import tempfile
from pathlib import Path

import pytest

from ShortsMaker import GenerateImage


def test_initialization_with_non_existent_file():
    with pytest.raises(FileNotFoundError):
        GenerateImage(config_file=Path("non_existent_file.yml"))


def test_initialization_with_invalid_file_format():
    with pytest.raises(ValueError):
        temp_path = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        temp_path = Path(temp_path.name)
        try:
            GenerateImage(config_file=temp_path)
        finally:
            temp_path.unlink()


def test_load_model_failure(generate_image):
    with pytest.raises(RuntimeError):
        generate_image._load_model("model_id")


def test_use_huggingface_flux_dev_success(generate_image):
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    temp_file = Path(temp_file.name)
    try:
        generate_image.use_huggingface_flux_dev(
            prompt="A lazy dog trying to eat a burger", output_path=temp_file.absolute()
        )
    finally:
        assert temp_file.exists()
        temp_file.unlink()


def test_use_huggingface_flux_schnell_success(generate_image):
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    temp_file = Path(temp_file.name)
    try:
        generate_image.use_huggingface_flux_schnell(
            prompt="A lazy dog trying to eat a burger", output_path=temp_file.absolute()
        )
    finally:
        assert temp_file.exists()
        temp_file.unlink()
