import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ShortsMaker.ask_llm import AskLLM, OllamaServiceManager, YoutubeDetails


@pytest.fixture
def mock_ollama_service_manager():
    """
    Fixture to provide a mocked instance of OllamaServiceManager.

    Returns:
        MagicMock: A mocked instance of OllamaServiceManager with predefined return values for start_service and stop_service methods.
    """
    ollama_service_manager = MagicMock(OllamaServiceManager)
    ollama_service_manager.start_service.return_value = True
    ollama_service_manager.stop_service.return_value = True
    return ollama_service_manager


@patch("ShortsMaker.ask_llm.AskLLM._load_llm_model")
def test_initialization_with_valid_config(
    mock_load_llm_model, setup_file, mock_ollama_service_manager
):
    mock_load_llm_model.return_value = None
    ask_llm = AskLLM(config_file=setup_file, model_name="test_model")
    assert ask_llm.model_name == "test_model"


def test_initialization_with_invalid_config_path():
    invalid_config_path = Path("temp.yml")
    with pytest.raises(FileNotFoundError):
        AskLLM(config_file=invalid_config_path)


def test_initialization_with_non_yaml_file(setup_file, tmp_path):
    with pytest.raises(ValueError):
        temp_path = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        temp_path = Path(temp_path.name)
        try:
            AskLLM(config_file=temp_path)
        finally:
            temp_path.unlink()


@patch("ShortsMaker.ask_llm.AskLLM._load_llm_model")
def test_llm_model_loading(mock_load_llm_model, mock_ollama_service_manager, setup_file):
    AskLLM(config_file=setup_file, model_name="test_model")
    mock_load_llm_model.assert_called_once_with("test_model", 0)


@patch("ShortsMaker.ask_llm.AskLLM._load_llm_model")
def test_invoke_creates_chat_prompt(mock_load_llm_model, setup_file, mock_ollama_service_manager):
    ask_llm = AskLLM(config_file=setup_file)
    ask_llm.ollama_service_manager = mock_ollama_service_manager
    ask_llm.llm = MagicMock()
    ask_llm.llm.with_structured_output.return_value = ask_llm.llm
    ask_llm.llm.invoke.return_value = {"title": "Test Title"}

    input_text = "Test script input."
    response = ask_llm.invoke(input_text=input_text)

    assert "title" in response
    ask_llm.llm.with_structured_output.assert_called_once_with(YoutubeDetails, include_raw=True)
    ask_llm.llm.invoke.assert_called_once()


@patch("ShortsMaker.ask_llm.AskLLM._load_llm_model")
@patch("ShortsMaker.ask_llm.OllamaServiceManager.stop_service")
@patch("ShortsMaker.ask_llm.subprocess.check_output")
@patch("ShortsMaker.ask_llm.subprocess.run")
def test_quit_llm_with_self_started_service(
    mock_load_llm_model,
    mock_stop_service,
    mock_check_output,
    mock_run,
    setup_file,
    mock_ollama_service_manager,
):
    mock_load_llm_model.return_value = None

    ask_llm = AskLLM(config_file=setup_file, model_name="test_model")
    ask_llm.self_started_ollama = True

    result = ask_llm.quit_llm()
    assert result is None
    mock_stop_service.assert_called_once()


@pytest.mark.skipif("RUNALL" not in os.environ, reason="takes too long")
def test_ask_llm_working(setup_file):
    script = "A video about a cat. Doing stunts like running around, flying, and jumping."
    ask_llm = AskLLM(config_file=setup_file)
    result = ask_llm.invoke(input_text=script)
    ask_llm.quit_llm()
    assert result["parsed"].title == "Feline Frenzy: Cat Stunt Master!"
    assert (
        result["parsed"].description
        == "Get ready for the most epic feline feats you've ever seen! Watch as our fearless feline friend runs, jumps, and even flies through a series of death-defying stunts."
    )
    assert result["parsed"].tags == ["cat", "stunts", "flying", "jumping"]
    assert (
        result["parsed"].thumbnail_description
        == "A cat in mid-air, performing a daring stunt with its paws outstretched, surrounded by a blurred cityscape with bright lights and colors."
    )
    assert result["parsing_error"] is None
    assert result is not None
