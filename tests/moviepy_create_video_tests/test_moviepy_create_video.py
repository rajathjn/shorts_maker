import random
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from moviepy import AudioFileClip, VideoFileClip

from ShortsMaker import MoviepyCreateVideo, VideoConfig


@pytest.fixture
def mock_audio_file(tmp_path):
    """Creates a mock audio file path."""
    audio_file = Path(__file__).parent.parent / "data" / "test.wav"
    return audio_file


@pytest.fixture
def mock_audio_clip():
    """Returns a mock AudioFileClip."""
    mock_clip = MagicMock(spec=AudioFileClip)
    mock_clip.duration = 10.0
    mock_clip.reader = MagicMock()
    mock_clip.reader.bitrate = 128
    return mock_clip


@pytest.fixture
def mock_video_clip():
    """Returns a mock VideoFileClip."""
    mock_clip = MagicMock(spec=VideoFileClip)
    mock_clip.duration = 20.0
    mock_clip.size = (1920, 1080)
    mock_clip.fps = 30
    mock_clip.reader = MagicMock()
    mock_clip.reader.bitrate = 5000
    return mock_clip


@pytest.fixture
def mock_font_file(tmp_path):
    """Creates a mock font file."""
    font_file = tmp_path / "test_font.ttf"
    font_file.touch()
    return font_file


@pytest.fixture
def mock_credits_files(tmp_path):
    """Creates mock credits files."""
    credits_dir = Path("assets/credits")
    return credits_dir


class TestMoviepyCreateVideo:
    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    def test_init_and_ffmpeg_verification(
        self, mock_subprocess_run, mock_get_logger, setup_file, mock_audio_file
    ):
        """Test initialization and FFmpeg verification."""
        # Setup
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Execute with context manager to ensure quit() is called
        with (
            patch("ShortsMaker.moviepy_create_video.AudioFileClip") as mock_audio_file_clip,
            patch("ShortsMaker.moviepy_create_video.VideoFileClip") as mock_video_file_clip,
            patch.object(MoviepyCreateVideo, "_load_transcript") as mock_load_transcript,
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript") as mock_preprocess,
            patch.object(
                MoviepyCreateVideo, "process_audio_transcript_to_word_and_sentences_transcript"
            ) as mock_process,
            patch.object(MoviepyCreateVideo, "prepare_background_video") as mock_prepare,
            patch.object(MoviepyCreateVideo, "_initialize_music") as mock_init_music,
            patch.object(MoviepyCreateVideo, "_initialize_font") as mock_init_font,
            patch.object(MoviepyCreateVideo, "_initialize_credits") as mock_init_credits,
        ):
            # Configure mocks
            mock_audio_file_clip.return_value = MagicMock()
            mock_audio_file_clip.return_value.reader.bitrate = 128
            mock_audio_file_clip.return_value.duration = 10.0

            mock_load_transcript.return_value = []
            mock_preprocess.return_value = []
            mock_process.return_value = ([], [])

            mock_video_file_clip.return_value = MagicMock()
            mock_video_file_clip.return_value.reader.bitrate = 5000
            mock_prepare.return_value = mock_video_file_clip.return_value

            mock_init_music.return_value = MagicMock()
            mock_init_music.return_value.reader.bitrate = 192

            mock_init_font.return_value = "test_font.ttf"
            mock_init_credits.return_value = MagicMock()

            # Execute
            creator = MoviepyCreateVideo(config_file=setup_file)

            # Assert
            mock_subprocess_run.assert_called_once_with(["ffmpeg", "-version"], check=True)
            mock_get_logger.assert_called_once_with("ShortsMaker.moviepy_create_video")

            # Verify required directories were accessed
            assert hasattr(creator, "video_dir")
            assert hasattr(creator, "music_dir")
            assert hasattr(creator, "fonts_dir")
            assert hasattr(creator, "credits_dir")

    def test_load_configuration(self, setup_file):
        """Test loading configuration from a YAML file."""
        config = MoviepyCreateVideo._load_configuration(setup_file)

        assert isinstance(config, VideoConfig)
        assert isinstance(config.cache_dir, Path)
        assert isinstance(config.assets_dir, Path)
        assert "output_audio_file" in config.audio_config
        assert "background_videos_urls" in config.video_config

    def test_load_configuration_invalid_file(self, tmp_path):
        """Test loading configuration with an invalid file."""
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.touch()

        with pytest.raises(ValueError, match="Invalid configuration file"):
            MoviepyCreateVideo._load_configuration(invalid_file)

    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    def test_initialize_audio_with_path(
        self, mock_subprocess_run, mock_get_logger, setup_file, mock_audio_file, mock_audio_clip
    ):
        """Test initializing audio with an explicit path."""
        with (
            patch(
                "ShortsMaker.moviepy_create_video.AudioFileClip", return_value=mock_audio_clip
            ) as mock_audio_file_clip,
            patch.object(MoviepyCreateVideo, "_initialize_background_video"),
            patch.object(MoviepyCreateVideo, "_load_transcript"),
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript"),
            patch.object(
                MoviepyCreateVideo,
                "process_audio_transcript_to_word_and_sentences_transcript",
                return_value=([], []),
            ),
            patch.object(MoviepyCreateVideo, "prepare_background_video"),
            patch.object(MoviepyCreateVideo, "_initialize_music"),
            patch.object(MoviepyCreateVideo, "_initialize_font"),
            patch.object(MoviepyCreateVideo, "_initialize_credits"),
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            MoviepyCreateVideo(config_file=setup_file, audio_path=str(mock_audio_file))

            mock_audio_file_clip.assert_called_once_with(str(mock_audio_file))
            mock_logger.info.assert_any_call(f"Audio Duration: {mock_audio_clip.duration:.2f}s")

    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    def test_initialize_audio_without_path(
        self, mock_subprocess_run, mock_get_logger, setup_file, mock_audio_file, mock_audio_clip
    ):
        """Test initializing audio without an explicit path."""
        with (
            patch(
                "ShortsMaker.moviepy_create_video.AudioFileClip", return_value=mock_audio_clip
            ) as mock_audio_file_clip,
            patch.object(MoviepyCreateVideo, "_initialize_background_video"),
            patch.object(MoviepyCreateVideo, "_load_transcript"),
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript"),
            patch.object(
                MoviepyCreateVideo,
                "process_audio_transcript_to_word_and_sentences_transcript",
                return_value=([], []),
            ),
            patch.object(MoviepyCreateVideo, "prepare_background_video"),
            patch.object(MoviepyCreateVideo, "_initialize_music"),
            patch.object(MoviepyCreateVideo, "_initialize_font"),
            patch.object(MoviepyCreateVideo, "_initialize_credits"),
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            # Check that it used the path from config
            expected_audio_path = Path(__file__).parent.parent / "data" / "test.wav"

            MoviepyCreateVideo(config_file=setup_file, audio_path=expected_audio_path)

            mock_audio_file_clip.assert_called_once_with(expected_audio_path)

    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    @patch("ShortsMaker.moviepy_create_video.download_youtube_video")
    def test_initialize_background_video_with_url(
        self,
        mock_download,
        mock_subprocess_run,
        mock_get_logger,
        mock_audio_clip,
        setup_file,
        mock_video_clip,
        tmp_path,
    ):
        """Test initializing background video with a URL."""
        with (
            patch(
                "ShortsMaker.moviepy_create_video.VideoFileClip", return_value=mock_video_clip
            ) as mock_video_file_clip,
            patch.object(MoviepyCreateVideo, "_initialize_audio", return_value=mock_audio_clip),
            patch.object(
                MoviepyCreateVideo,
                "process_audio_transcript_to_word_and_sentences_transcript",
                return_value=([], []),
            ),
            patch.object(MoviepyCreateVideo, "_load_transcript"),
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript"),
            patch.object(
                MoviepyCreateVideo, "prepare_background_video", return_value=mock_video_clip
            ),
            patch.object(MoviepyCreateVideo, "_initialize_music"),
            patch.object(MoviepyCreateVideo, "_initialize_font"),
            patch.object(MoviepyCreateVideo, "_initialize_credits"),
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Mock the download function to return a list of video paths
            test_video_path = tmp_path / "test_video.mp4"
            mock_download.return_value = [test_video_path]

            # Mock random.choice to always pick the first URL
            with patch("random.choice", side_effect=lambda x: x[0]):
                MoviepyCreateVideo(config_file=setup_file)

            # Verify download was called with the right URL
            mock_download.assert_called_once()
            assert mock_download.call_args[0][0] == "https://www.youtube.com/watch?v=n_Dv4JMiwK8"

            # Verify VideoFileClip was initialized with the right path
            mock_video_file_clip.assert_called_once_with(test_video_path, audio=False)

    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    def test_initialize_background_video_with_path(
        self,
        mock_subprocess_run,
        mock_get_logger,
        mock_audio_clip,
        setup_file,
        mock_video_clip,
        tmp_path,
    ):
        """Test initializing background video with an explicit path."""
        video_path = tmp_path / "test_video.mp4"
        video_path.touch()

        with (
            patch(
                "ShortsMaker.moviepy_create_video.VideoFileClip", return_value=mock_video_clip
            ) as mock_video_file_clip,
            patch.object(MoviepyCreateVideo, "_initialize_audio", return_value=mock_audio_clip),
            patch.object(
                MoviepyCreateVideo,
                "process_audio_transcript_to_word_and_sentences_transcript",
                return_value=([], []),
            ),
            patch.object(MoviepyCreateVideo, "_load_transcript"),
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript"),
            patch.object(
                MoviepyCreateVideo, "prepare_background_video", return_value=mock_video_clip
            ),
            patch.object(MoviepyCreateVideo, "_initialize_music"),
            patch.object(MoviepyCreateVideo, "_initialize_font"),
            patch.object(MoviepyCreateVideo, "_initialize_credits"),
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            MoviepyCreateVideo(config_file=setup_file, bg_video_path=str(video_path))

            mock_video_file_clip.assert_called_once_with(str(video_path), audio=False)

    def test_select_random_color(self):
        """Test selecting a random color."""
        # Set a fixed seed for reproducibility
        random.seed(42)

        # Get a color
        color = MoviepyCreateVideo._select_random_color()

        # Check that the result is a tuple of 4 integers (RGBA)
        assert isinstance(color, tuple)
        assert len(color) == 4
        assert all(isinstance(c, int) for c in color)
        assert all(0 <= c <= 255 for c in color)

    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    def test_load_transcript(
        self, mock_subprocess_run, mock_get_logger, mock_audio_clip, setup_file
    ):
        """Test loading a transcript file."""
        with (
            patch.object(MoviepyCreateVideo, "_initialize_audio", return_value=mock_audio_clip),
            patch.object(
                MoviepyCreateVideo,
                "process_audio_transcript_to_word_and_sentences_transcript",
                return_value=([], []),
            ),
            patch.object(MoviepyCreateVideo, "_initialize_background_video"),
            patch.object(MoviepyCreateVideo, "prepare_background_video"),
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript"),
            patch.object(MoviepyCreateVideo, "_initialize_music"),
            patch.object(MoviepyCreateVideo, "_initialize_font"),
            patch.object(MoviepyCreateVideo, "_initialize_credits"),
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            creator = MoviepyCreateVideo(config_file=setup_file)

            # Mock the transcript path
            transcript_path = Path(creator.config.cache_dir) / "transcript.json"

            # Call the method directly
            transcript = creator._load_transcript(transcript_path)

            # Verify the transcript is a list
            assert isinstance(transcript, list)

    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    def test_initialize_font_with_provided_path(
        self, mock_subprocess_run, mock_get_logger, mock_audio_clip, setup_file, mock_font_file
    ):
        """Test initializing font with an explicit path."""
        with (
            patch.object(MoviepyCreateVideo, "_initialize_audio", return_value=mock_audio_clip),
            patch.object(
                MoviepyCreateVideo,
                "process_audio_transcript_to_word_and_sentences_transcript",
                return_value=([], []),
            ),
            patch.object(MoviepyCreateVideo, "_initialize_background_video"),
            patch.object(MoviepyCreateVideo, "prepare_background_video"),
            patch.object(MoviepyCreateVideo, "_load_transcript"),
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript"),
            patch.object(MoviepyCreateVideo, "_initialize_music"),
            patch.object(MoviepyCreateVideo, "_initialize_credits"),
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            creator = MoviepyCreateVideo(config_file=setup_file, font_path=str(mock_font_file))

            assert creator.font_path == str(mock_font_file)

    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    def test_initialize_font_without_path(
        self, mock_subprocess_run, mock_get_logger, mock_audio_clip, setup_file, mock_font_file
    ):
        """Test initializing font without an explicit path."""
        with (
            patch.object(MoviepyCreateVideo, "_initialize_audio", return_value=mock_audio_clip),
            patch.object(
                MoviepyCreateVideo,
                "process_audio_transcript_to_word_and_sentences_transcript",
                return_value=([], []),
            ),
            patch.object(MoviepyCreateVideo, "_initialize_background_video"),
            patch.object(MoviepyCreateVideo, "prepare_background_video"),
            patch.object(MoviepyCreateVideo, "_load_transcript"),
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript"),
            patch.object(MoviepyCreateVideo, "_initialize_music"),
            patch.object(MoviepyCreateVideo, "_initialize_credits"),
            patch.object(MoviepyCreateVideo, "_select_random_color", return_value=(0, 0, 0, 0)),
            patch("random.choice", return_value=mock_font_file),
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            creator = MoviepyCreateVideo(config_file=setup_file)

            # The font path should be the absolute path to the mock_font_file
            assert creator.font_path == mock_font_file.absolute()

    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    def test_initialize_credits(
        self, mock_subprocess_run, mock_get_logger, mock_audio_clip, setup_file, mock_credits_files
    ):
        """Test initializing credits files."""
        with (
            patch.object(MoviepyCreateVideo, "_initialize_audio", return_value=mock_audio_clip),
            patch.object(
                MoviepyCreateVideo,
                "process_audio_transcript_to_word_and_sentences_transcript",
                return_value=([], []),
            ),
            patch.object(MoviepyCreateVideo, "_initialize_background_video"),
            patch.object(MoviepyCreateVideo, "prepare_background_video"),
            patch.object(MoviepyCreateVideo, "_load_transcript"),
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript"),
            patch.object(MoviepyCreateVideo, "_initialize_music"),
            patch.object(MoviepyCreateVideo, "_initialize_font"),
            patch("ShortsMaker.moviepy_create_video.VideoFileClip") as mock_video_file_clip,
        ):
            # Create mock VideoFileClip instances for the credits and mask
            mock_credits = MagicMock()
            mock_mask = MagicMock()
            mock_masked_credits = MagicMock()

            # Configure the mock to return different objects for different calls
            mock_video_file_clip.side_effect = [mock_mask, mock_credits]

            # Configure the to_mask method to return the mask
            mock_mask.to_mask.return_value = mock_mask

            # Configure the with_mask method to return the masked credits
            mock_credits.with_mask.return_value = mock_masked_credits

            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            creator = MoviepyCreateVideo(config_file=setup_file, credits_path=mock_credits_files)

            # Check that the calls were made correctly
            mock_video_file_clip.assert_any_call(
                mock_credits_files / "credits_mask.mp4", audio=False
            )
            mock_video_file_clip.assert_any_call(mock_credits_files / "credits.mp4", audio=False)

            # The masked credits should be returned
            assert creator.credits_video is mock_masked_credits

    def test_preprocess_audio_transcript(self):
        """Test preprocessing audio transcript."""
        # Create a sample transcript
        transcript = [
            {"word": "Hello", "start": 0.0, "end": 1.1},
            {"word": "world", "start": 1.5, "end": 2.2},
            {"word": "this", "start": 2.5, "end": 3.0},
        ]

        # Create a mock instance with this transcript
        mock_instance = MagicMock()
        mock_instance.audio_transcript = transcript

        # Call the method
        result = MoviepyCreateVideo.preprocess_audio_transcript(mock_instance)

        # Check that end times have been updated to match the start time of the next segment
        assert result[0]["end"] == 1.5
        assert result[1]["end"] == 2.5
        # The last segment's end time should remain unchanged
        assert result[2]["end"] == 3.0

    def test_process_audio_transcript_to_word_and_sentences_transcript(self):
        """Test processing audio transcript to word and sentences transcripts."""
        # Create a sample transcript
        transcript = [
            {"word": "Hello", "start": 0.0, "end": 1.0},
            {"word": "world.", "start": 1.0, "end": 2.0},
            {"word": "This", "start": 2.0, "end": 3.0},
            {"word": "is", "start": 3.0, "end": 4.0},
            {"word": "a", "start": 4.0, "end": 5.0},
            {"word": "test.", "start": 5.0, "end": 6.0},
        ]

        # Create a mock instance with this transcript
        mock_instance = MagicMock()
        mock_instance.audio_transcript = transcript
        mock_instance.PUNCTUATION_MARKS = [".", ";", ":", "!", "?", ","]
        mock_instance.logger = MagicMock()

        # Call the method
        word_transcript, sentences_transcript = (
            MoviepyCreateVideo.process_audio_transcript_to_word_and_sentences_transcript(
                mock_instance
            )
        )

        # Check word transcript
        assert len(word_transcript) == 6
        assert word_transcript[0]["word"] == "Hello "

        # Check sentences transcript
        assert len(sentences_transcript) == 2
        assert sentences_transcript[0]["sentence"] == "Hello world. "
        assert sentences_transcript[1]["sentence"] == "This is a test. "

    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    def test_prepare_background_video(
        self, mock_subprocess_run, mock_get_logger, setup_file, mock_video_clip, mock_audio_clip
    ):
        """Test preparing the background video."""
        with (
            patch.object(MoviepyCreateVideo, "_initialize_audio", return_value=mock_audio_clip),
            patch.object(
                MoviepyCreateVideo,
                "process_audio_transcript_to_word_and_sentences_transcript",
                return_value=([], []),
            ),
            patch.object(
                MoviepyCreateVideo, "_initialize_background_video", return_value=mock_video_clip
            ),
            patch.object(MoviepyCreateVideo, "_load_transcript"),
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript"),
            patch.object(MoviepyCreateVideo, "_initialize_music"),
            patch.object(MoviepyCreateVideo, "_initialize_font"),
            patch.object(MoviepyCreateVideo, "_initialize_credits"),
            patch("random.uniform", return_value=10.0),
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Configure mocks for video processing methods
            mock_video_clip.subclipped.return_value = mock_video_clip
            mock_video_clip.cropped.return_value = mock_video_clip
            mock_video_clip.with_effects.return_value = mock_video_clip

            creator = MoviepyCreateVideo(config_file=setup_file)
            creator.bg_video = mock_video_clip
            creator.audio_clip = mock_audio_clip
            creator.delay = 1
            creator.fade_time = 2

            # Verify the video processing methods were called
            mock_video_clip.subclipped.assert_called_once()
            mock_video_clip.cropped.assert_called_once()
            mock_video_clip.with_effects.assert_called_once()

    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    def test_create_text_clips(
        self, mock_subprocess_run, mock_get_logger, setup_file, mock_video_clip, mock_audio_clip
    ):
        """Test creating text clips."""
        with (
            patch.object(MoviepyCreateVideo, "_initialize_audio", return_value=mock_audio_clip),
            patch.object(MoviepyCreateVideo, "_initialize_background_video"),
            patch.object(MoviepyCreateVideo, "prepare_background_video"),
            patch.object(MoviepyCreateVideo, "_load_transcript"),
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript"),
            patch.object(
                MoviepyCreateVideo,
                "process_audio_transcript_to_word_and_sentences_transcript",
                return_value=([], []),
            ),
            patch.object(MoviepyCreateVideo, "_initialize_music"),
            patch.object(MoviepyCreateVideo, "_initialize_font"),
            patch.object(MoviepyCreateVideo, "_initialize_credits"),
            patch("ShortsMaker.moviepy_create_video.TextClip") as mock_text_clip,
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Create a mock text clip
            mock_clip = MagicMock()
            mock_clip.with_start.return_value = mock_clip
            mock_clip.with_end.return_value = mock_clip
            mock_clip.with_position.return_value = mock_clip
            mock_text_clip.return_value = mock_clip

            creator = MoviepyCreateVideo(config_file=setup_file)
            creator.bg_video = mock_video_clip
            creator.word_transcript = [
                {"word": "Hello", "start": 0.0, "end": 1.0},
                {"word": "world", "start": 1.0, "end": 2.0},
            ]
            creator.delay = 1
            creator.font_path = "test_font.ttf"
            creator.color = (255, 255, 255, 255)
            creator.text_clips = []

            # Call the method
            result = creator.create_text_clips()

            # There should be two text clips created
            assert len(result) == 2
            assert mock_text_clip.call_count == 2

    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    def test_prepare_audio(
        self, mock_subprocess_run, mock_get_logger, setup_file, mock_video_clip, mock_audio_clip
    ):
        """Test preparing audio."""
        with (
            patch.object(MoviepyCreateVideo, "_initialize_audio", return_value=mock_audio_clip),
            patch.object(MoviepyCreateVideo, "_initialize_background_video"),
            patch.object(MoviepyCreateVideo, "prepare_background_video"),
            patch.object(MoviepyCreateVideo, "_load_transcript"),
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript"),
            patch.object(
                MoviepyCreateVideo,
                "process_audio_transcript_to_word_and_sentences_transcript",
                return_value=([], []),
            ),
            patch.object(MoviepyCreateVideo, "_initialize_music"),
            patch.object(MoviepyCreateVideo, "_initialize_font"),
            patch.object(MoviepyCreateVideo, "_initialize_credits"),
            patch("ShortsMaker.moviepy_create_video.CompositeAudioClip") as mock_composite_audio,
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Create mock audio clips
            mock_music = MagicMock()
            mock_music.with_effects.return_value = mock_music

            mock_audio = MagicMock()
            mock_audio.with_start.return_value = mock_audio

            # Create mock composite audio
            mock_composite = MagicMock()
            mock_composite_audio.return_value = mock_composite

            creator = MoviepyCreateVideo(config_file=setup_file)
            creator.bg_video = mock_video_clip
            creator.audio_clip = mock_audio
            creator.music_clip = mock_music
            creator.fade_time = 2
            creator.delay = 1

            # Call the method
            result = creator.prepare_audio()

            # Verify effects were applied
            assert mock_music.with_effects.call_count == 3
            mock_audio.with_start.assert_called_once_with(1)

            # Verify composite audio was created
            mock_composite_audio.assert_called_once_with([mock_music, mock_audio])
            assert result is mock_composite

    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    def test_call(
        self, mock_subprocess_run, mock_get_logger, setup_file, mock_video_clip, mock_audio_clip
    ):
        """Test the __call__ method."""
        with (
            patch.object(MoviepyCreateVideo, "_initialize_audio", return_value=mock_audio_clip),
            patch.object(MoviepyCreateVideo, "_initialize_background_video"),
            patch.object(MoviepyCreateVideo, "_load_transcript"),
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript"),
            patch.object(
                MoviepyCreateVideo,
                "process_audio_transcript_to_word_and_sentences_transcript",
                return_value=([], []),
            ),
            patch.object(
                MoviepyCreateVideo, "prepare_background_video", return_value=mock_video_clip
            ),
            patch.object(MoviepyCreateVideo, "_initialize_music"),
            patch.object(MoviepyCreateVideo, "_initialize_font"),
            patch.object(MoviepyCreateVideo, "_initialize_credits"),
            patch.object(MoviepyCreateVideo, "create_text_clips") as mock_create_text,
            patch.object(MoviepyCreateVideo, "prepare_audio") as mock_prepare_audio,
            patch("ShortsMaker.moviepy_create_video.max", return_value=128),
            patch("ShortsMaker.moviepy_create_video.CompositeVideoClip") as mock_composite_video,
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Configure mocks
            mock_text_clips = [MagicMock(), MagicMock()]
            mock_create_text.return_value = mock_text_clips

            mock_final_audio = MagicMock()
            mock_prepare_audio.return_value = mock_final_audio

            mock_final_video = MagicMock()
            mock_composite_video.return_value = mock_final_video
            mock_final_video.with_audio.return_value = mock_final_video

            # Create instance and call
            creator = MoviepyCreateVideo(config_file=setup_file, add_credits=False)
            creator.bg_video = mock_video_clip
            result = creator("output.mp4")

            # Verify correct method calls
            mock_create_text.assert_called_once()
            mock_prepare_audio.assert_called_once()
            mock_composite_video.assert_called_once_with([mock_video_clip] + mock_text_clips)
            mock_final_video.with_audio.assert_called_once_with(mock_final_audio)
            mock_final_video.write_videofile.assert_called_once_with(
                "output.mp4",
                codec="mpeg4",
                bitrate="5000k",
                fps=30,
                audio_bitrate="128k",
                preset="medium",
                threads=8,
            )

            assert result

    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    def test_quit(self, mock_subprocess_run, mock_get_logger, setup_file, mock_audio_clip):
        """Test the quit method for proper cleanup of resources."""
        with (
            patch.object(MoviepyCreateVideo, "_initialize_audio", return_value=mock_audio_clip),
            patch.object(
                MoviepyCreateVideo,
                "process_audio_transcript_to_word_and_sentences_transcript",
                return_value=([], []),
            ),
            patch.object(MoviepyCreateVideo, "_initialize_background_video"),
            patch.object(MoviepyCreateVideo, "prepare_background_video"),
            patch.object(MoviepyCreateVideo, "_load_transcript"),
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript"),
            patch.object(MoviepyCreateVideo, "_initialize_music"),
            patch.object(MoviepyCreateVideo, "_initialize_font"),
            patch.object(MoviepyCreateVideo, "_initialize_credits"),
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Create instance with mock resources
            creator = MoviepyCreateVideo(config_file=setup_file)

            # Create mock clips
            mock_audio_clip = MagicMock()
            mock_bg_video = MagicMock()
            mock_music_clip = MagicMock()
            mock_credits_video = MagicMock()
            mock_credit_video_mask = MagicMock()

            # Set mock clips as instance attributes
            creator.audio_clip = mock_audio_clip
            creator.bg_video = mock_bg_video
            creator.music_clip = mock_music_clip
            creator.credits_video = mock_credits_video
            creator.credit_video_mask = mock_credit_video_mask

            # Add some test attributes
            creator.test_attr = "test"

            # Call quit method
            creator.quit()

            # Verify all clips were closed
            mock_audio_clip.close.assert_called_once()
            mock_bg_video.close.assert_called_once()
            mock_music_clip.close.assert_called_once()
            mock_credits_video.close.assert_called_once()
            mock_credit_video_mask.close.assert_called_once()

            # Verify debug logs were called
            mock_logger.debug.assert_any_call("Resources successfully cleaned up.")

            # Verify attributes were deleted
            assert not hasattr(creator, "test_attr")
            assert not hasattr(creator, "audio_clip")
            assert not hasattr(creator, "bg_video")
            assert not hasattr(creator, "music_clip")
            assert not hasattr(creator, "credits_video")
            assert not hasattr(creator, "credit_video_mask")

            # Verify logger was preserved
            assert hasattr(creator, "logger")

    @patch("ShortsMaker.moviepy_create_video.get_logger")
    @patch("subprocess.run")
    def test_quit_with_errors(
        self, mock_subprocess_run, mock_get_logger, setup_file, mock_audio_clip
    ):
        """Test the quit method handles errors gracefully during cleanup."""
        with (
            patch.object(MoviepyCreateVideo, "_initialize_audio", return_value=mock_audio_clip),
            patch.object(
                MoviepyCreateVideo,
                "process_audio_transcript_to_word_and_sentences_transcript",
                return_value=([], []),
            ),
            patch.object(MoviepyCreateVideo, "prepare_background_video"),
            patch.object(MoviepyCreateVideo, "_load_transcript"),
            patch.object(MoviepyCreateVideo, "preprocess_audio_transcript"),
            patch.object(MoviepyCreateVideo, "_initialize_music"),
            patch.object(MoviepyCreateVideo, "_initialize_font"),
            patch.object(MoviepyCreateVideo, "_initialize_credits"),
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Create instance with mock resources
            creator = MoviepyCreateVideo(config_file=setup_file)

            # Create mock clip that raises an exception on close
            mock_problematic_clip = MagicMock()
            mock_problematic_clip.close.side_effect = Exception("Test error")

            # Set mock clip as instance attribute
            creator.audio_clip = mock_problematic_clip

            # Call quit method
            creator.quit()

            # Verify error was logged
            mock_logger.error.assert_any_call("Error closing resources: Test error")

            # Verify cleanup completed despite error
            mock_logger.debug.assert_called_with("Resources successfully cleaned up.")

            # Verify problematic attribute was attempted to be deleted
            assert not hasattr(creator, "audio_clip")
