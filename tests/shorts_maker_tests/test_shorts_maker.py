import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from ShortsMaker import ShortsMaker


def test_validate_config_path_valid(tmp_path):
    config_path = tmp_path / "config.yml"
    config_path.touch()

    with pytest.raises(TypeError):
        maker = ShortsMaker(config_path)
        assert maker.setup_cfg == config_path


def test_validate_config_path_invalid_extension(tmp_path):
    config_path = tmp_path / "config.txt"
    config_path.touch()

    with pytest.raises(ValueError):
        ShortsMaker(config_path)


def test_validate_config_path_not_found():
    with pytest.raises(FileNotFoundError):
        ShortsMaker(Path("/nonexistent/config.yml"))


@patch("ShortsMaker.ShortsMaker.is_unique_submission")
@patch("praw.Reddit")
def test_get_reddit_post(mock_reddit, mock_is_unique_submission, shorts_maker):
    mock_submission = MagicMock()
    mock_submission.title = "Test Title"
    mock_submission.selftext = "Test Content"
    mock_submission.name = "t3_123abc"
    mock_submission.id = "123abc"
    mock_submission.url = "https://reddit.com/r/test/123abc"

    mock_subreddit = MagicMock()
    mock_subreddit.hot.return_value = [mock_submission]
    mock_subreddit.title = "Test Subreddit"
    mock_subreddit.display_name = "test"

    mock_is_unique_submission.return_value = True
    mock_reddit.return_value.subreddit.return_value = mock_subreddit

    result = shorts_maker.get_reddit_post()
    assert "Test Title" in result
    assert "Test Content" in result


@patch("praw.Reddit")
def test_get_reddit_post_with_url(mock_reddit, shorts_maker):
    # Mock submission data
    mock_submission = MagicMock()
    mock_submission.title = "Test Title from URL"
    mock_submission.selftext = "Test Content from URL"
    mock_submission.name = "t3_url_submission"
    mock_submission.id = "url_submission"
    mock_submission.url = "https://www.reddit.com/r/random_subreddit/test_title_from_url/"

    # Mock Reddit API response
    mock_reddit.return_value.submission.return_value = mock_submission

    # Test with URL
    test_url = "https://www.reddit.com/r/random_subreddit/test_title_from_url/"
    result = shorts_maker.get_reddit_post(url=test_url)

    # Assertions
    assert "Test Title from URL" in result
    assert "Test Content from URL" in result
    mock_reddit.return_value.submission.assert_called_once_with(url=test_url)


@patch("ShortsMaker.shorts_maker.tts")
def test_generate_audio_success(mock_tts, shorts_maker, tmp_path):
    # Test successful audio generation
    source_text = "Test text for audio generation"
    output_audio = tmp_path / "test_output.wav"
    output_script = tmp_path / "test_script.txt"
    seed = "en_us_001"

    mock_tts.return_value = None

    result = shorts_maker.generate_audio(
        source_text, output_audio=output_audio, output_script_file=output_script, seed=seed
    )

    assert result is True
    mock_tts.assert_called_once()


@patch("ShortsMaker.shorts_maker.tts")
def test_generate_audio_failure(mock_tts, shorts_maker):
    # Test failed audio generation
    source_text = "Test text for audio generation"
    mock_tts.side_effect = Exception("TTS Failed")

    result = shorts_maker.generate_audio(source_text)

    assert result is False
    mock_tts.assert_called_once()


@patch("secrets.choice")
def test_generate_audio_random_speaker(mock_choice, shorts_maker):
    # Test random speaker selection when no seed provided
    mock_choice.return_value = "en_us_001"
    source_text = "Test text"

    with patch("ShortsMaker.shorts_maker.tts"):
        shorts_maker.generate_audio(source_text)
        mock_choice.assert_called_once()


def test_generate_audio_text_processing(shorts_maker):
    # Test text processing functionality
    source_text = "Test123 text AITA for YTA"
    output_script = shorts_maker.cache_dir / "test_script.txt"

    with patch("ShortsMaker.shorts_maker.tts"):
        shorts_maker.generate_audio(source_text, output_script_file=output_script)

        with open(output_script) as f:
            processed_text = f.read()

        # Verify text processing
        assert "Test 123" in processed_text
        assert "Am I the asshole" in processed_text
        assert "You're the Asshole" in processed_text


@patch("ShortsMaker.shorts_maker.generate_audio_transcription")
def test_generate_audio_transcript(mock_transcription, shorts_maker, tmp_path):
    # Setup test files
    source_audio = tmp_path / "test.wav"
    source_audio.touch()
    source_text = tmp_path / "test.txt"
    source_text.write_text("Test transcript text")
    output_file = tmp_path / "transcript.json"

    # Setup mock transcription response
    mock_transcript = [
        {"word": "Test", "start": 0.1, "end": 0.3},
        {"word": "transcript", "start": 0.4, "end": 0.6},
        {"word": "text", "start": 0.7, "end": 0.9},
    ]
    mock_transcription.return_value = mock_transcript

    # Call function
    result = shorts_maker.generate_audio_transcript(
        source_audio, source_text, output_transcript_file=str(output_file), debug=False
    )

    # Verify mock was called with correct args
    mock_transcription.assert_called_once_with(
        audio_file=str(source_audio),
        script="Test transcript text",
        device=shorts_maker.audio_cfg["device"],
        model=shorts_maker.audio_cfg["model"],
        batch_size=shorts_maker.audio_cfg["batch_size"],
        compute_type=shorts_maker.audio_cfg["compute_type"],
    )

    # Verify result contains filtered transcript
    assert result == mock_transcript

    # Verify transcript was saved to file
    with open(output_file) as f:
        saved_transcript = yaml.safe_load(f)
    assert saved_transcript == mock_transcript


@patch("ShortsMaker.shorts_maker.generate_audio_transcription")
def test_generate_audio_transcript_default_output(mock_generate_audio_transcription, shorts_maker):
    # Test default output file name generation
    source_audio = Path(__file__).parent.parent / "data" / "test.wav"
    source_text = Path(__file__).parent.parent / "data" / "test.txt"
    with open(Path(__file__).parent.parent / "data" / "transcript.json") as f:
        expected_transcript = yaml.safe_load(f)

    mock_generate_audio_transcription.return_value = expected_transcript
    result = shorts_maker.generate_audio_transcript(source_audio, source_text)

    expected_output = shorts_maker.cache_dir / shorts_maker.audio_cfg["transcript_json"]
    assert expected_output.exists()
    mock_generate_audio_transcription.assert_called_once()
    assert result == expected_transcript


@pytest.mark.skipif("RUNALL" not in os.environ, reason="takes too long")
def test_generate_audio_transcript_with_whisperx(shorts_maker):
    # Test default output file name generation
    source_audio = Path(__file__).parent.parent / "data" / "test.wav"
    source_text = Path(__file__).parent.parent / "data" / "test.txt"
    with open(Path(__file__).parent.parent / "data" / "transcript.json") as f:
        expected_transcript = yaml.safe_load(f)

    result = shorts_maker.generate_audio_transcript(source_audio, source_text)

    expected_output = shorts_maker.cache_dir / shorts_maker.audio_cfg["transcript_json"]
    assert expected_output.exists()
    assert result == expected_transcript


def test_filter_word_transcript(shorts_maker):
    test_transcript = [
        {"word": "valid", "start": 0.1, "end": 0.3},
        {"word": "invalid1", "start": 0, "end": 0.5},
        {"word": "invalid2", "start": 0.1, "end": 5.5},
        {"word": "valid2", "start": 1.0, "end": 1.2},
    ]

    filtered = shorts_maker._filter_word_transcript(test_transcript)

    assert len(filtered) == 2
    assert filtered[0]["word"] == "valid"
    assert filtered[1]["word"] == "valid2"
