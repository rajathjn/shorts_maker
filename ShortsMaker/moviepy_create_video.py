import logging
import random
import secrets
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    afx,
    vfx,
)

from .utils import (
    COLORS_DICT,
    download_youtube_music,
    download_youtube_video,
    setup_package_logging,
)

random.seed(secrets.randbelow(1000000))


@dataclass
class VideoConfig:
    cache_dir: Path
    assets_dir: Path
    audio_config: dict
    video_config: dict
    logging_config: dict


class MoviepyCreateVideo:
    """
    Class for creating videos from media components using MoviePy.

    This class facilitates the creation of videos by integrating various media
    components such as background videos, audio tracks, music, fonts, and credits.
    It provides settings for fading effects, delays, and logging during video
    generation. It ensures proper initialization and handling of required
    directories, configurations, and external dependencies like FFmpeg.
    The class allows flexibility in providing media paths or configuring the
    video creation process dynamically.

    Attributes:
        DEFAULT_FADE_TIME (int): Default duration for fade effects applied to the video.
        DEFAULT_DELAY (int): Default delay applied between video transitions or sections.
        DEFAULT_LOGGING_CONFIG (dict): Default logging configurations for the video generation process.
        REQUIRED_DIRECTORIES (list): List of essential directories required for using the class.
        PUNCTUATION_MARKS (list): List of punctuation marks used for processing transcripts or text inputs.
    """

    DEFAULT_FADE_TIME = 2
    DEFAULT_DELAY = 2
    DEFAULT_LOGGING_CONFIG = {
        "log_file": "generate_video.log",
        "logger_name": "MoviepyCreateVideo",
        "level": logging.INFO,
        "enable": True,
    }
    REQUIRED_DIRECTORIES = ["video_dir", "music_dir", "fonts_dir", "credits_dir"]
    PUNCTUATION_MARKS = [".", ";", ":", "!", "?", ","]

    def __init__(
        self,
        config_file: Path | str,
        logging_config: defaultdict = None,
        bg_video_path: Path | str = None,
        credits_path: Path | str = None,
        audio_path: Path | str = None,
        music_path: Path | str = None,
        transcript_path: Path | str = None,
        font_path: Path | str = None,
        fade_time: int = DEFAULT_FADE_TIME,
        delay: int = DEFAULT_DELAY,
    ) -> None:
        self.fade_time = fade_time
        self.delay = delay

        # Initialize configuration
        self.config = self._load_configuration(config_file)
        self.logger = self._setup_logging(logging_config)
        self._verify_ffmpeg()

        # Initialize directories
        self._setup_directories()

        # Initialize media components
        self.audio_clip = self._initialize_audio(audio_path)
        self.audio_clip_bitrate = self.audio_clip.reader.bitrate

        self.audio_transcript = self._load_transcript(transcript_path)
        self.audio_transcript = self.preprocess_audio_transcript()
        self.word_transcript, self.sentences_transcript = (
            self.process_audio_transcript_to_word_and_sentences_transcript()
        )

        self.bg_video = self._initialize_background_video(bg_video_path)
        self.bg_video = self.prepare_background_video()
        self.bg_video_bitrate = self.bg_video.reader.bitrate

        self.music_clip = self._initialize_music(music_path)
        self.music_clip_bitrate = self.music_clip.reader.bitrate

        self.font_path = self._initialize_font(font_path)

        self.credits_video = self._initialize_credits(credits_path)

        # Initialize color
        self.color = self._select_random_color()
        self.logger.info(f"Using color {self.color}")

    @staticmethod
    def _load_configuration(config_file: Path | str) -> VideoConfig:
        """
        Loads and validates a YAML configuration file, and then parses its content
        into a `VideoConfig` object. The method checks for the existence of the file
        and ensures that it has the correct `.yml` extension. If the validation fails,
        it raises a `ValueError`. Otherwise, the YAML content is loaded and used to
        instantiate a `VideoConfig` with the appropriate properties.

        Args:
            config_file: The path to the configuration file provided as a `Path` object
                or a `str`. The file must exist and have a `.yml` extension.

        Returns:
            A `VideoConfig` object created using the data parsed from the provided
            configuration file.

        Raises:
            ValueError: If the configuration file does not exist or does not have a
                `.yml` extension.
        """
        config_path = Path(config_file)
        if not config_path.exists() or config_path.suffix != ".yml":
            raise ValueError(f"Invalid configuration file: {config_path}")

        with open(config_path) as f:
            cfg = yaml.safe_load(f)

        return VideoConfig(
            cache_dir=Path(cfg["cache_dir"]),
            assets_dir=Path(cfg["assets_dir"]),
            audio_config=cfg.get("audio", {}),
            video_config=cfg.get("video", {}),
            logging_config=cfg.get("logging", {}),
        )

    def _setup_logging(self, logging_config: defaultdict = None) -> logging.Logger:
        """
        Configures and initializes the logging setup for the package using the provided or default
        logging configuration.

        Combines the default logging configuration with the user-specified configuration
        and applies the setup using the `setup_package_logging` function.

        Args:
            logging_config (defaultdict, optional): A dictionary of specific logging
                configurations to override or supplement the default logging setup. If
                not provided, the default logging configuration will be used.

        Returns:
            logging.Logger: The primary logger instance configured for the package.
        """
        final_config = self.DEFAULT_LOGGING_CONFIG.copy()
        final_config.update(self.config.logging_config)
        if logging_config:
            final_config.update(logging_config)
        return setup_package_logging(**final_config)

    def _verify_ffmpeg(self) -> None:
        """
        Verifies the availability of the FFmpeg utility on the system.

        This method checks if FFmpeg is installed and available in the system's PATH
        environment variable. It does so by attempting to execute the FFmpeg command
        with the `-version` argument, which displays FFmpeg's version details. If
        FFmpeg is not installed or cannot be accessed, an error is logged, and the
        exception is re-raised for further handling.

        Raises:
            Exception: If FFmpeg is not installed or available in the PATH. The specific
            exception raised during the failure will also be re-raised.
        """
        try:
            import subprocess

            subprocess.run(["ffmpeg", "-version"], check=True)
        except Exception as e:
            self.logger.error("ffmpeg is not installed or not available in path")
            raise e

    def _setup_directories(self) -> None:
        """
        Sets up the necessary directories for storing assets used in the application.

        This method configures various directories such as those for background
        videos, background music, fonts, and credits. Additionally, it ensures
        that the directories required for background videos and background music
        are created if they do not already exist.

        Attributes:
            video_dir: Path to the directory where background videos are stored.
            music_dir: Path to the directory where background music is stored.
            fonts_dir: Path to the directory where fonts are stored.
            credits_dir: Path to the directory where credits data is stored.

        Raises:
            FileNotFoundError: If the base assets directory does not exist or is
                inaccessible during operation.
        """
        self.video_dir = self.config.assets_dir / "background_videos"
        self.music_dir = self.config.assets_dir / "background_music"
        self.fonts_dir = self.config.assets_dir / "fonts"
        self.credits_dir = self.config.assets_dir / "credits"

        for directory in [self.video_dir, self.music_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def _initialize_audio(self, audio_path: Path | str = None) -> AudioFileClip:
        """
        Initializes the audio by loading an audio file from the specified path or a default
        directory set in the configuration. If no audio path is provided, the method will
        attempt to find an audio file in the configured cache directory.

        Args:
            audio_path (Path | str, optional): The path to the audio file. If None, the method
                will use the `cache_dir` and `output_audio_file` settings from the
                configuration to locate the audio file.

        Returns:
            AudioFileClip: An instance of AudioFileClip initialized with the located audio file.

        Raises:
            ValueError: If no `audio_path` is provided and the `audio_config` in the
                configuration does not specify an `output_audio_file` key.
        """
        if audio_path is None:
            self.logger.info(
                f"No audio path provided. Using the audio directory {self.config.cache_dir} to find an audio file."
            )
            if "output_audio_file" not in self.config.audio_config:
                raise ValueError("Missing 'output_audio_file' in 'audio' section in setup.yml")
            audio_path = self.config.cache_dir / self.config.audio_config["output_audio_file"]
            self.logger.info(f"Using audio file {audio_path}")
        return AudioFileClip(audio_path)

    def _initialize_background_video(self, bg_video_path: Path | str = None) -> VideoFileClip:
        """
        Initializes the background video for further video processing.

        If a `bg_video_path` is not explicitly provided, the method will attempt to use the URLs specified
        in the video configuration to download a random background video. The downloaded video path will
        then be used to initialize the `VideoFileClip` instance. If the video configuration does not
        contain `background_videos_urls`, a ValueError is raised.

        Args:
            bg_video_path (Path | str, optional): The path to the background video file. If None, a
                video is chosen or downloaded based on the configuration.

        Raises:
            ValueError: If `background_videos_urls` is missing in the video configuration.

        Returns:
            VideoFileClip: The background video instance without audio.
        """
        if bg_video_path is None:
            self.logger.info(
                "No background video path provided. Using the background_videos_urls to download a background video."
            )
            if "background_videos_urls" not in self.config.video_config:
                raise ValueError("Missing 'background_videos_urls' in 'video' section in setup.yml")
            # choose a random url
            bg_video_url = random.choice(self.config.video_config["background_videos_urls"])
            self.logger.info(f"Using bg_video_url {bg_video_url}")
            bg_videos_path = download_youtube_video(
                bg_video_url,
                self.video_dir,
            )
            bg_video_path = random.choice(bg_videos_path).absolute()
            self.logger.info(f"Using bg_video_path {bg_video_path}")
        return VideoFileClip(bg_video_path, audio=False)

    @staticmethod
    def _select_random_color() -> tuple[int, int, int, int]:
        """
        Selects a random color from a pre-defined dictionary of colors.

        This method accesses a dictionary containing color codes, selects a random
        key from the dictionary, and retrieves the corresponding color value. It is
        used to dynamically choose colors for various operations requiring random
        color assignments.

        Returns:
            tuple[int, int, int, int]: A tuple representing the RGBA color values,
            where each value corresponds to red, green, blue, and alpha channels.

        Raises:
            KeyError: If the dictionary is empty or an invalid key is accessed.
        """
        return COLORS_DICT[random.choice(list(COLORS_DICT.keys()))]

    def _load_transcript(self, transcript_path: Path | str) -> list[dict[str, Any]]:
        """
        Loads and parses a transcript file in YAML format. The function determines the path of the
        transcript file, either based on the provided argument or through the configuration setup.
        It ensures the path validity and raises appropriate errors if the file cannot be found or
        if key configuration fields are missing. If the transcript file exists, it reads and
        deserializes its content into a Python list of dictionaries.

        Args:
            transcript_path (Path | str): Path to the transcript file. If None, this argument will
                default to a path derived from the configuration settings.

        Raises:
            ValueError: If `transcript_path` is None and configuration settings do not specify
                'transcript_json' in the 'audio' section of `setup.yml`.
            ValueError: If the resolved `transcript_path` does not exist or the file cannot be found.

        Returns:
            list[dict[str, Any]]: The content of the transcript file parsed as a list of dictionaries.
        """
        if transcript_path is None:
            self.logger.info(
                f"No transcript path provided. Using the audio directory {self.config.cache_dir} to find a transcript file."
            )
            if "transcript_json" not in self.config.audio_config:
                raise ValueError("Missing 'transcript_json' in 'audio' section in setup.yml")
            transcript_path = self.config.cache_dir / self.config.audio_config["transcript_json"]
            self.logger.info(f"Using transcript file {transcript_path}")
        path = Path(transcript_path)
        if not path.exists():
            raise ValueError(f"Transcript file not found: {path}")

        with open(transcript_path) as audio_transcript_file:
            return yaml.safe_load(audio_transcript_file)

    def _initialize_music(self, music_path: Path | str) -> AudioFileClip:
        """
        Initializes and loads a music file, handling cases where the music path is not provided
        by downloading music from a specified source.

        If a music path is not given, a random URL is selected from the list of background music
        URLs defined in the video configuration, and the corresponding music file is downloaded
        and set as the music path. Ensures the music file exists before returning it as an
        AudioFileClip object.

        Args:
            music_path (Path | str): The path to the music file to be loaded. If None, the method
                will attempt to download and use a file from a configured URL.

        Returns:
            AudioFileClip: An AudioFileClip object representing the loaded music file.

        Raises:
            ValueError: If the `background_music_urls` is missing in the video configuration when
                no `music_path` is provided, or if the specified music file does not exist.
        """
        if music_path is None:
            self.logger.info(
                "No music path provided. Using the background_music_urls to download a background music."
            )
            if "background_music_urls" not in self.config.video_config:
                raise ValueError("Missing 'background_music_urls' in 'video' section in setup.yml")
            # choose a random url
            music_url = random.choice(self.config.video_config["background_music_urls"])
            self.logger.info(f"Using music_url {music_url}")
            musics_path = download_youtube_music(
                music_url,
                self.music_dir,
            )
            music_path = random.choice(musics_path).absolute()
            self.logger.info(f"Using music_path {music_path}")
        path = Path(music_path)
        if not path.exists():
            raise ValueError(f"Music file not found: {path}")

        return AudioFileClip(path)

    def _initialize_font(self, font_path: Path | str) -> str:
        """
        Initializes and selects a font file for use, either provided explicitly or chosen
        from a predefined directory of font files.

        If the input `font_path` is not provided, a random `.ttf` file is selected from
        the directory. If the directory does not contain any `.ttf` files, the function raises
        an exception. If `font_path` is supplied but points to a non-existent file, an exception
        is also raised.

        Args:
            font_path (Path | str): The path to the font file to be initialized. If None,
                a font is randomly selected from the predefined font directory.

        Raises:
            ValueError: Raised when no font files exist in the predefined font directory,
                or when the given `font_path` does not exist.

        Returns:
            str: The absolute path of the selected font file, ensuring any valid input font
            file or selected file from the directory is returned in string format.
        """
        if font_path is None:
            self.logger.info(
                f"No font path provided. Using the fonts directory {self.fonts_dir} to find a font."
            )
            font_files = list(self.fonts_dir.glob("*.ttf"))
            if not font_files:
                raise ValueError(f"No font files found in {self.fonts_dir}")
            return random.choice(font_files).absolute()
        path = Path(font_path)
        if not path.exists():
            raise ValueError(f"Font file not found: {path}")
        return str(path)

    def _initialize_credits(self, credits_path: Path | str) -> VideoFileClip:
        """
        Initializes the credits video by either using a provided path or searching a default credits directory.
        Raises an error if no valid credits file is found or if the provided path does not exist.
        Additionally, applies a mask to the credits video if a corresponding mask file exists.

        Args:
            credits_path (Path | str): The path to the credits video file or directory. If None,
                the function will attempt to locate a credits file in the default credits directory.

        Returns:
            VideoFileClip: The VideoFileClip object of the credits video with the applied mask.

        Raises:
            FileNotFoundError: If no credits files are found in the default credits directory.
            ValueError: If the given credits_path does not exist.
        """
        if credits_path is None:
            self.logger.info(
                f"No credits path provided. Using the credits directory {self.credits_dir} to find a credits file."
            )
            credit_videos = list(self.credits_dir.glob("*.mp4"))
            if not credit_videos:
                raise FileNotFoundError("No credits files found in the credits directory")
            credits_path = self.credits_dir
            self.logger.info(f"Using credits file {credits_path}")

        path = Path(credits_path)
        if not path.exists():
            raise ValueError(f"Credits file not found: {path}")

        self.credit_video_mask: VideoFileClip = VideoFileClip(
            path / "credits_mask.mp4", audio=False
        ).to_mask()

        return VideoFileClip(path / "credits.mp4", audio=False).with_mask(self.credit_video_mask)

    def preprocess_audio_transcript(self) -> list[dict[str, Any]]:
        """
        Preprocesses the audio transcript to adjust segment boundaries.

        This method modifies the transcript by updating the "end" time of each audio
        segment to match the "start" time of the subsequent segment. This ensures that
        audio segments are properly aligned in cases where boundaries are not explicitly
        defined. The original transcript is updated in-place and returned.

        Returns:
            list[dict[str, Any]]: The updated list of audio transcript segments,
            each represented as a dictionary containing at least "start" and "end" keys.

        """
        for i in range(len(self.audio_transcript) - 1):
            self.audio_transcript[i]["end"] = self.audio_transcript[i + 1]["start"]
        return self.audio_transcript

    def process_audio_transcript_to_word_and_sentences_transcript(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Processes audio transcript data into individual word-level and sentence-level
        transcripts. The method parses the `audio_transcript` to create two lists: a
        word transcript and a sentences transcript. Each word and sentence transcript
        contains details such as text, start time, and end time. Sentences are delimited
        based on specific punctuation marks defined in `PUNCTUATION_MARKS`. If an error
        occurs during word processing, it logs the error using the `logger` attribute.

        Returns:
            tuple[list[dict[str, Any]], list[dict[str, Any]]]: A tuple containing two
            lists. The first list is the word transcript, where each item contains
            information about individual words and their start and end times. The second
            list is the sentences transcript, where each item contains information about
            sentences, including the sentence text and its start and end times.
        """
        word_transcript = []
        sentences_transcript = []

        sentence_start = 0
        sentence_end = 0

        word_start = 0
        word_end = 0

        sentence = ""

        for count, transcript in enumerate(self.audio_transcript):
            word = transcript["word"].strip()
            sentence += word + " "

            word_end = transcript["end"]
            word_transcript.append(
                {
                    "word": sentence,
                    "start": word_start,
                    "end": word_end,
                }
            )
            word_start = word_end

            try:
                if word[-1] in self.PUNCTUATION_MARKS and word != "...":
                    sentence_end = word_end
                    sentences_transcript.append(
                        {
                            "sentence": sentence,
                            "start": sentence_start,
                            "end": sentence_end,
                        }
                    )
                    sentence_start = sentence_end
                    sentence = ""
            except Exception as e:
                self.logger.error(f"Error processing word '{word}': {e}")

        # Add final sentence if any remains
        if sentence != "":
            sentences_transcript.append(
                {
                    "sentence": sentence,
                    "start": sentence_start,
                    "end": sentence_end,
                }
            )

        return word_transcript, sentences_transcript

    def prepare_background_video(self) -> VideoFileClip:
        """
        Prepares and processes a background video clip for use in a composition.

        This function modifies the background video clip by randomly selecting a segment,
        cropping it to a specific aspect ratio, applying crossfade effects, and logging relevant
        information about the original and processed video dimensions.

        Returns:
            VideoFileClip: The processed and modified video clip ready for use in further processing.

        Args:
            self: The instance of the class containing this method.

        Raises:
            AttributeError: If attributes such as `self.bg_video`, `self.audio_clip`, or `self.logger`
                are not properly defined in the class.
            ValueError: If the random start time exceeds the duration of the background video.
        """
        width, height = self.bg_video.size

        self.logger.info(
            f"Original video - Width: {width}, Height: {height}, FPS: {self.bg_video.fps}"
        )

        # Select random segment of appropriate length
        random_start = random.uniform(20, self.bg_video.duration - self.audio_clip.duration - 20)
        random_end = random_start + self.audio_clip.duration

        self.logger.info(f"Using video segment from {random_start:.2f}s to {random_end:.2f}s")

        # Crop and apply effects
        self.bg_video = (
            self.bg_video.subclipped(
                start_time=random_start - self.delay, end_time=random_end + self.delay
            )
            .cropped(x_center=width / 2, width=height * 9 / 16)
            .with_effects([vfx.CrossFadeIn(self.fade_time), vfx.CrossFadeOut(self.fade_time)])
        )

        new_width, new_height = self.bg_video.size
        self.logger.info(
            f"Processed video - Width: {new_width}, Height: {new_height}, FPS: {self.bg_video.fps}"
        )

        return self.bg_video

    def create_text_clips(self) -> list[TextClip]:
        """
        Creates a list of text clips for use in video editing.

        This method generates text clips based on a word transcript where each word is associated with its start and end
        time. These text clips are created with specific stylistic properties such as font size, color, background color,
        alignment, and other visual attributes. The generated clips are then appended to the object's `text_clips` list
        and returned.

        Returns:
            list[TextClip]: A list of TextClip objects representing the visualized words with specified styling and timing.
        """
        for word in self.word_transcript:
            clip = (
                TextClip(
                    font=self.font_path,
                    text=word["word"],
                    font_size=int(0.06 * self.bg_video.size[0]),
                    size=(int(0.8 * self.bg_video.size[0]), int(0.8 * self.bg_video.size[0])),
                    color=self.color,
                    bg_color=(0, 0, 0, 100),
                    text_align="center",
                    method="caption",
                    stroke_color="black",
                    stroke_width=1,
                    transparent=True,
                )
                .with_start(word["start"] + self.delay)
                .with_end(word["end"] + self.delay)
                .with_position(("center", "center"))
            )

            self.text_clips.append(clip)

        return self.text_clips

    def prepare_audio(self) -> CompositeAudioClip:
        """
        Processes and combines audio clips to prepare the final audio track.

        This method applies a series of effects to a music clip, including looping to match
        the duration of a background video, adjusting the volume, and adding fade-in and fade-out
        effects. Additionally, it modifies the start time of another audio clip to introduce
        a delay. Once processed, it combines the music clip and the audio clip into a single
        composite audio track.

        Returns:
            CompositeAudioClip: A combined audio clip that includes the processed music and
            audio components.
        """
        # Process music clip
        self.music_clip = self.music_clip.with_effects(
            [
                afx.AudioLoop(duration=self.bg_video.duration),
                afx.MultiplyVolume(factor=0.05),
                afx.AudioFadeIn(self.fade_time),
                afx.AudioFadeOut(self.fade_time),
            ]
        )
        self.audio_clip = self.audio_clip.with_start(self.delay)

        # Combine audio clips
        return CompositeAudioClip([self.music_clip, self.audio_clip])

    def __call__(
        self,
        output_path: str = "output.mp4",
        codec: str = "mpeg4",
        preset: str = "medium",
        threads: int = 8,
    ) -> bool:
        """
        Executes the video processing pipeline by assembling all video and audio elements,
        creating a composite video, and writing the final output to a file. The method allows
        customization of output file properties such as codec, preset, and threading.

        Args:
            output_path (str): The path to save the output video file. Defaults to "output.mp4".
            codec (str): The video codec to use for encoding the output video. Defaults to "mpeg4".
            preset (str): The compression preset to optimize encoding speed vs quality. Defaults to "medium".
            threads (int): The number of threads to use during encoding. Defaults to 8.

        Returns:
            bool: Returns True upon successful creation and saving of the video.
        """
        # Create video clips
        self.video_clips: list[VideoFileClip | TextClip] = [self.bg_video]
        self.text_clips: list[TextClip] = []
        self.text_clips = self.create_text_clips()
        self.video_clips.extend(self.text_clips)

        # Add the credits clip to the end of the video
        self.credits_video = self.credits_video.resized(width=int(0.8 * self.bg_video.size[0]))
        self.video_clips.append(
            self.credits_video.with_start(
                self.bg_video.duration - self.credits_video.duration
            ).with_position(("center", "bottom"))
        )

        # Combine video clips
        output_video = CompositeVideoClip(self.video_clips)

        # Prepare final audio
        output_audio = self.prepare_audio()

        # Create final video
        final_video = output_video.with_audio(output_audio)

        # Write output file
        final_video.write_videofile(
            output_path,
            codec=codec,
            bitrate=f"{self.bg_video_bitrate}k",
            fps=self.bg_video.fps,
            audio_bitrate=f"{max(self.music_clip_bitrate, self.audio_clip_bitrate)}k",
            preset=preset,
            threads=threads,
        )
        self.logger.info(f"Video successfully created at {output_path}")
        output_video.close()
        output_audio.close()
        final_video.close()

        return True

    def quit(self) -> None:
        """
        Closes and cleans up resources used by the instance.

        This method ensures that all open files, clips, or other resources associated
        with the instance are properly closed and the corresponding instance variables
        are deleted. It handles exceptions gracefully, logging any issues encountered
        during the cleanup process.

        Raises:
            Exception: If an error occurs while closing a resource or deleting
            an attribute, it will log the error details.
        """
        try:
            # Close any open files or clips
            if hasattr(self, "audio_clip") and self.audio_clip:
                self.audio_clip.close()
            if hasattr(self, "bg_video") and self.bg_video:
                self.bg_video.close()
            if hasattr(self, "music_clip") and self.music_clip:
                self.music_clip.close()
            if hasattr(self, "credits_video") and self.credits_video:
                self.credits_video.close()
            if hasattr(self, "credit_video_mask") and self.credit_video_mask:
                self.credit_video_mask.close()
        except Exception as e:
            self.logger.error(f"Error closing resources: {e}")

        # Delete all instance variables
        for attr in list(self.__dict__.keys()):
            try:
                self.logger.debug(f"Deleting {attr}")
                if attr == "logger":
                    continue
                delattr(self, attr)
            except Exception as e:
                self.logger.error(f"Error deleting {attr}: {e}")

        self.logger.debug("Resources successfully cleaned up.")
        return
