from unittest.mock import Mock, patch

import pytest

from ShortsMaker.utils.get_tts import (
    ENDPOINT_DATA,
    VOICES,
    _process_chunks,
    _split_text,
    _validate_inputs,
    tts,
)


@pytest.fixture
def mock_audio_segment():
    with patch("pydub.AudioSegment.from_file") as mock:
        yield mock


def test_validate_inputs_valid():
    _validate_inputs("test text", VOICES[0])
    # Should not raise any exception


def test_validate_inputs_invalid_voice():
    with pytest.raises(ValueError, match="voice must be valid"):
        _validate_inputs("test text", "invalid_voice")


def test_validate_inputs_empty_text():
    with pytest.raises(ValueError, match="text must not be 'None'"):
        _validate_inputs("", VOICES[0])


def test_split_text():
    text = "This is a test text that needs to be split into multiple chunks"
    chunks = _split_text(text, chunk_size=20)
    assert len(chunks) > 1
    assert all(len(chunk) <= 20 for chunk in chunks)


@patch("requests.post")
def test_process_chunks_success(mock_post):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "fake_base64_data"}
    mock_post.return_value = mock_response

    chunks = ["test chunk"]
    endpoint = {"url": "test_url", "response": "data"}
    voice = VOICES[0]
    audio_data = [""]

    result = _process_chunks(chunks, endpoint, voice, audio_data)
    assert result == ["fake_base64_data"]


@patch("requests.post")
def test_process_chunks_failure(mock_post):
    mock_response = Mock()
    mock_response.status_code = 404
    mock_post.return_value = mock_response

    chunks = ["test chunk"]
    endpoint = {"url": "test_url", "response": "data"}
    voice = VOICES[0]
    audio_data = [""]

    result = _process_chunks(chunks, endpoint, voice, audio_data)
    assert result is None


@patch("pydub.AudioSegment.from_file")
@patch("requests.post")
def test_tts_integration(mock_post, mock_audio):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "ZmFrZV9iYXNlNjRfZGF0YQ=="}
    mock_post.return_value = mock_response

    mock_audio_obj = Mock()
    mock_audio_obj.export = Mock()
    mock_audio.return_value = mock_audio_obj

    tts("test text", VOICES[0], "test_output.wav")
    assert mock_audio_obj.export.called


@patch("requests.post")
@patch("ShortsMaker.utils.get_tts._save_audio")
def test_tts_with_failing_and_successful_endpoints(mock_save_audio, mock_post):
    # Mock responses for endpoints
    def mock_post_side_effect(url, json, headers) -> Mock:
        if url == ENDPOINT_DATA[0]["url"]:
            # Simulate failure for the first endpoint
            response = Mock()
            response.status_code = 500
            return response
        elif url == ENDPOINT_DATA[1]["url"]:
            # Simulate success for the second endpoint
            response = Mock()
            response.status_code = 200
            response.json.return_value = {ENDPOINT_DATA[1]["response"]: "mock_audio_data"}
            return response

    mock_post.side_effect = mock_post_side_effect

    mock_save_audio.return_value = None

    # Input data
    text = "This is a test."
    voice = "en_us_001"
    output_filename = "test_output.mp3"

    # Call the tts function
    tts(text, voice, output_filename)

    # Assertions
    assert mock_post.call_count == 2
    mock_post.assert_any_call(
        ENDPOINT_DATA[0]["url"],
        json={"text": "This is a test.", "voice": voice},
        headers={
            "User-Agent": "com.zhiliaoapp.musically/2022600030 (Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)",
        },
    )
    mock_post.assert_any_call(
        ENDPOINT_DATA[1]["url"],
        json={"text": "This is a test.", "voice": voice},
        headers={
            "User-Agent": "com.zhiliaoapp.musically/2022600030 (Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)",
        },
    )
    mock_save_audio.assert_called_once_with(["mock_audio_data"], output_filename)
