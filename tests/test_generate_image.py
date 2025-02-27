import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ShortsMaker import GenerateImage


@pytest.fixture
def generate_image(setup_file):
    """Fixture to initialize and return a GenerateImage instance.

    Args:
        setup_file: The configuration file for GenerateImage.

    Returns:
        GenerateImage: An instance of the GenerateImage class.
    """
    return GenerateImage(setup_file)


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


@patch("ShortsMaker.generate_image.GenerateImage._load_model")
def test_use_huggingface_flux_dev_success(mock_load_model, generate_image):
    mock_load_model.return_value = True
    generate_image.pipe = MagicMock()
    generate_image.use_huggingface_flux_dev(prompt="Random stuff", output_path="random_path.png")


@patch("ShortsMaker.generate_image.GenerateImage._load_model")
def test_use_huggingface_flux_schnell_success(mock_load_model, generate_image):
    mock_load_model.return_value = True
    generate_image.pipe = MagicMock()
    generate_image.use_huggingface_flux_schnell(
        prompt="Random stuff", output_path="random_path.png"
    )
