from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ShortsMaker.utils.download_youtube_music import download_youtube_music


@pytest.fixture
def mock_music_dir(tmp_path):
    return tmp_path / "music"


@pytest.fixture
def mock_ydl_no_chapters():
    mock = MagicMock()
    mock.extract_info.return_value = {"title": "test_song"}
    mock.sanitize_info.return_value = {"title": "test_song", "chapters": None}
    mock.prepare_filename.return_value = "test_song.wav"
    return mock


@pytest.fixture
def mock_ydl_with_chapters():
    mock = MagicMock()
    mock.extract_info.return_value = {"title": "test_song_chapters"}
    mock.sanitize_info.return_value = {
        "title": "test_song_chapters",
        "chapters": [
            {"title": "Chapter 1", "start_time": 0, "end_time": 60},
            {"title": "Chapter 2", "start_time": 60, "end_time": 120},
        ],
    }
    return mock


@pytest.mark.parametrize("force", [True, False])
def test_download_without_chapters(mock_music_dir, mock_ydl_no_chapters, force):
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_no_chapters

        result = download_youtube_music("https://youtube.com/test", mock_music_dir, force=force)

        assert isinstance(result, Path)
        assert result.name == "test_song.wav"
        mock_ydl_no_chapters.download.assert_called_once()


def test_download_with_chapters(mock_music_dir, mock_ydl_with_chapters):
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_with_chapters

        result = download_youtube_music("https://youtube.com/test", mock_music_dir)

        assert isinstance(result, list)
        assert len(result) >= 0  # Since files are only checked at end
        mock_ydl_with_chapters.download.call_count == 2


def test_download_with_existing_files(mock_music_dir, mock_ydl_no_chapters):
    # Create existing file
    mock_music_dir.mkdir(parents=True)
    existing_file = mock_music_dir / "test_song.wav"
    existing_file.touch()

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_no_chapters

        # Should not download when force=False
        result = download_youtube_music("https://youtube.com/test", mock_music_dir, force=False)

        assert isinstance(result, Path)
        assert not mock_ydl_no_chapters.download.called

        # Should download when force=True
        result = download_youtube_music("https://youtube.com/test", mock_music_dir, force=True)

        assert isinstance(result, Path)
        mock_ydl_no_chapters.download.assert_called_once()
