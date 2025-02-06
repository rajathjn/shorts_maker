from unittest.mock import MagicMock, patch

import pytest

from ShortsMaker.ask_llm import OllamaServiceManager


@pytest.fixture
def ollama_service_manager(mock_logger):
    """Fixture to provide an instance of OllamaServiceManager with a mock logger.

    Args:
        mock_logger: A mock logger for the OllamaServiceManager.

    Returns:
        An instance of OllamaServiceManager.
    """
    return OllamaServiceManager(logger=mock_logger)


def test_initialization(ollama_service_manager):
    assert ollama_service_manager.logger.name == "OllamaServiceManager"


@patch("ShortsMaker.ask_llm.subprocess.Popen")
@patch("ShortsMaker.ask_llm.time.sleep", return_value=None)
def test_start_service(mock_sleep, mock_popen, ollama_service_manager):
    process_mock = MagicMock()
    process_mock.poll.return_value = None
    mock_popen.return_value = process_mock

    result = ollama_service_manager.start_service()
    assert result is True
    mock_popen.assert_called_once()


@patch("ShortsMaker.ask_llm.subprocess.run")
def test_stop_service_on_windows(mock_subprocess_run, ollama_service_manager):
    ollama_service_manager.process = MagicMock()
    ollama_service_manager.system = "windows"
    result = ollama_service_manager.stop_service()
    assert result is True
    mock_subprocess_run.assert_called()


@patch("ShortsMaker.ask_llm.psutil.process_iter")
def test_is_ollama_running(mock_process_iter, ollama_service_manager):
    mock_process_iter.return_value = [
        MagicMock(info={"name": "Ollama"}),
    ]
    result = ollama_service_manager.is_ollama_running()
    assert result is True


def test_is_service_running_with_active_process(ollama_service_manager):
    ollama_service_manager.process = MagicMock()
    ollama_service_manager.process.poll.return_value = None

    result = ollama_service_manager.is_service_running()
    assert result is True


@patch("ShortsMaker.ask_llm.subprocess.check_output")
def test_stop_running_model(mock_check_output, ollama_service_manager):
    model_name = "test_model"
    mock_check_output.return_value = "Stopped"

    result = ollama_service_manager.stop_running_model(model_name)
    assert result is True
    mock_check_output.assert_called_with(["ollama", "stop", model_name], stderr=-2, text=True)


@patch("ShortsMaker.ask_llm.ollama.ps")
def test_get_running_models(mock_ollama_ps, ollama_service_manager):
    mock_ollama_ps.return_value = ["model1", "model2"]

    result = ollama_service_manager.get_running_models()
    assert result == ["model1", "model2"]


@patch("ShortsMaker.ask_llm.ollama.pull")
def test_get_llm_model(mock_ollama_pull, ollama_service_manager):
    model_name = "test_model"
    mock_ollama_pull.return_value = "model_data"

    result = ollama_service_manager.get_llm_model(model_name)
    assert result == "model_data"
    mock_ollama_pull.assert_called_with(model_name)


@patch("ShortsMaker.ask_llm.ollama.list")
def test_get_list_of_downloaded_files(mock_ollama_list, ollama_service_manager):
    mock_ollama_list.return_value = [("models", [MagicMock(), MagicMock(), MagicMock()])]
    mock_ollama_list.return_value[0][1][0].model = "submodel1"
    mock_ollama_list.return_value[0][1][1].model = "submodel2"
    mock_ollama_list.return_value[0][1][2].model = "submodel3"

    result = ollama_service_manager.get_list_of_downloaded_files()
    assert result == ["submodel1", "submodel2", "submodel3"]
