from unittest.mock import MagicMock, patch

import pytest

from ShortsMaker.utils.audio_transcript import (
    align_transcript_with_script,
    generate_audio_transcription,
)


def test_align_transcript_with_script_basic():
    transcript = [
        {"text": "hello world", "start": 0.0, "end": 1.0},
        {"text": "how are you", "start": 1.0, "end": 2.0},
    ]
    script = "hello world how are you today"

    result = align_transcript_with_script(transcript, script)

    assert len(result) == 2
    assert result[0]["text"] == "hello world"
    assert result[1]["text"] == "how are you"
    assert result[0]["start"] == 0.0
    assert result[0]["end"] == 1.0
    assert result[1]["start"] == 1.0
    assert result[1]["end"] == 2.0


def test_align_transcript_with_script_partial_match():
    transcript = [
        {"text": "helo wrld", "start": 0.0, "end": 1.0},  # Misspelled
        {"text": "how r u", "start": 1.0, "end": 2.0},  # Text speak
    ]
    script = "hello world how are you"

    result = align_transcript_with_script(transcript, script)

    assert len(result) == 2
    assert result[0]["text"] == "hello world"
    assert result[1]["text"] == "how"


def test_align_transcript_empty_inputs():
    transcript = []
    script = "hello world"

    result = align_transcript_with_script(transcript, script)
    assert result == []

    transcript = [{"text": "hello", "start": 0.0, "end": 1.0}]
    script = ""

    result = align_transcript_with_script(transcript, script)
    assert len(result) == 1
    assert result[0]["text"] == "hello"


def test_align_transcript_with_longer_script():
    transcript = [
        {"text": "this is", "start": 0.0, "end": 1.0},
        {"text": "a test", "start": 1.0, "end": 2.0},
    ]
    script = "this is a test with extra words at the end"

    result = align_transcript_with_script(transcript, script)

    assert len(result) == 2
    assert result[0]["text"] == "this is"
    assert result[1]["text"] == "a test"
    assert all(["start" in entry and "end" in entry for entry in result])


def test_align_transcript_timing_preserved():
    transcript = [
        {"text": "first segment", "start": 1.5, "end": 2.5},
        {"text": "second segment", "start": 2.5, "end": 3.5},
    ]
    script = "first segment second segment"

    result = align_transcript_with_script(transcript, script)

    assert len(result) == 2
    assert result[0]["start"] == 1.5
    assert result[0]["end"] == 2.5
    assert result[1]["start"] == 2.5
    assert result[1]["end"] == 3.5


@pytest.fixture
def mock_whisperx():
    with patch("ShortsMaker.utils.audio_transcript.whisperx") as mock_wx:
        # Mock the load_model and model.transcribe
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [{"text": "hello world", "start": 0.0, "end": 1.0}],
            "language": "en",
        }
        mock_wx.load_model.return_value = mock_model

        # Mock load_audio
        mock_wx.load_audio.return_value = "audio_data"

        # Mock alignment model and align
        mock_align_model = MagicMock()
        mock_metadata = MagicMock()
        mock_wx.load_align_model.return_value = (mock_align_model, mock_metadata)
        mock_wx.align.return_value = {
            "segments": [
                {
                    "words": [
                        {"word": "hello", "start": 0.0, "end": 0.5},
                        {"word": "world", "start": 0.5, "end": 1.0},
                    ]
                }
            ]
        }
        yield mock_wx


def test_generate_audio_transcription_basic(mock_whisperx):
    # Test basic functionality
    result = generate_audio_transcription(
        audio_file="test.wav", script="hello world", device="cpu", batch_size=8
    )

    assert len(result) == 2
    assert result[0]["word"] == "hello"
    assert result[0]["start"] == 0.0
    assert result[0]["end"] == 0.5
    assert result[1]["word"] == "world"
    assert result[1]["start"] == 0.5
    assert result[1]["end"] == 1.0


def test_generate_audio_transcription_model_cleanup(mock_whisperx):
    with patch("ShortsMaker.utils.audio_transcript.gc") as mock_gc:
        with patch("ShortsMaker.utils.audio_transcript.torch") as mock_torch:
            mock_torch.cuda.is_available.return_value = True

            generate_audio_transcription(audio_file="test.wav", script="hello world")

            # Verify cleanup calls
            assert mock_gc.collect.call_count == 2
            assert mock_torch.cuda.empty_cache.call_count == 2


def test_generate_audio_transcription_missing_timestamps(mock_whisperx):
    # Mock align to return words without timestamps
    mock_whisperx.align.return_value = {
        "segments": [{"words": [{"word": "hello"}, {"word": "world", "start": 0.5, "end": 1.0}]}]
    }

    result = generate_audio_transcription(audio_file="test.wav", script="hello world")

    assert len(result) == 2
    assert result[0]["word"] == "hello"
    assert "start" in result[0]
    assert "end" in result[0]
    assert result[1]["word"] == "world"
    assert result[1]["start"] == 0.5
    assert result[1]["end"] == 1.0


def test_generate_audio_transcription_parameters(mock_whisperx):
    # Test if parameters are correctly passed
    generate_audio_transcription(
        audio_file="test.wav",
        script="test script",
        device="test_device",
        batch_size=32,
        compute_type="float32",
        model="medium",
    )

    mock_whisperx.load_model.assert_called_with("medium", "test_device", compute_type="float32")

    mock_whisperx.load_align_model.assert_called_with(language_code="en", device="test_device")
