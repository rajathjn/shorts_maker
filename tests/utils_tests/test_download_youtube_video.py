from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ShortsMaker.utils.download_youtube_video import download_youtube_video


@pytest.fixture
def mock_ydl():
    with patch("yt_dlp.YoutubeDL") as mock:
        mock_instance = Mock()
        mock.return_value.__enter__.return_value = mock_instance
        mock_instance.extract_info.return_value = {"title": "test_video"}
        mock_instance.sanitize_info.return_value = {"title": "test_video"}
        mock_instance.prepare_filename.return_value = "test_video.mp4"
        yield mock_instance


@pytest.fixture
def tmp_path_with_video(tmp_path):
    video_file = tmp_path / "test_video.mp4"
    video_file.touch()
    return tmp_path


def test_download_video_success(mock_ydl, tmp_path):
    url = "https://www.youtube.com/watch?v=test123"

    result = download_youtube_video(url, tmp_path)

    mock_ydl.extract_info.assert_called_once_with(url, download=False)
    mock_ydl.download.assert_called_once_with([url])
    assert isinstance(result, list)
    assert all(isinstance(p, Path) for p in result)


def test_download_video_existing_file(mock_ydl, tmp_path_with_video):
    url = "https://www.youtube.com/watch?v=test123"

    result = download_youtube_video(url, tmp_path_with_video)

    mock_ydl.extract_info.assert_called_once_with(url, download=False)
    mock_ydl.download.assert_not_called()
    assert isinstance(result, list)
    assert len(result) == 1
    assert all(isinstance(p, Path) for p in result)


def test_download_video_force(mock_ydl, tmp_path_with_video):
    url = "https://www.youtube.com/watch?v=test123"

    result = download_youtube_video(url, tmp_path_with_video, force=True)

    mock_ydl.extract_info.assert_called_once_with(url, download=False)
    mock_ydl.download.assert_called_once_with([url])
    assert isinstance(result, list)
    assert all(isinstance(p, Path) for p in result)


def test_download_video_no_files(mock_ydl, tmp_path):
    url = "https://www.youtube.com/watch?v=test123"
    mock_ydl.prepare_filename.return_value = str(tmp_path / "nonexistent.mp4")

    result = download_youtube_video(url, tmp_path)

    assert isinstance(result, list)
    assert len(result) == 0
