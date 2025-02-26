import logging
import random
import secrets
from collections import defaultdict
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
    colors_dict,
    download_youtube_music,
    download_youtube_video,
    setup_package_logging,
)

random.seed(secrets.randbelow(1000000))


class MoviepyCreateVideo:
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
        fade_time: int = 2,
        delay: int = 2,
    ) -> None:
        self.fade_time = fade_time
        self.delay = delay

        self.setup_cfg = Path(config_file) if isinstance(config_file, str) else config_file
        if not self.setup_cfg.exists():
            raise FileNotFoundError(f"File {str(self.setup_cfg)} does not exist")

        if self.setup_cfg.suffix != ".yml":
            raise ValueError(f"File {str(self.setup_cfg)} is not a yaml file")

        # load the yml file
        with open(self.setup_cfg) as f:
            self.cfg = yaml.safe_load(f)

        # check if logging is set up in config_file
        self.logging_cfg = {
            "log_file": "generate_video.log",
            "logger_name": "MoviepyCreateVideo",
            "level": logging.INFO,
            "enable": True,
        }

        if "logging" in self.cfg:
            # override with values in from the setup.yml file
            for key, value in self.cfg["logging"].items():
                self.logging_cfg[key] = value

        if logging_config is not None:
            # override with values defined in logging_config
            for key, value in logging_config.items():
                self.logging_cfg[key] = value

        self.logger = setup_package_logging(**self.logging_cfg)

        # Check if ffmpeg is installed and available in path
        try:
            import subprocess

            subprocess.run(["ffmpeg", "-version"], check=True)
        except Exception as e:
            self.logger.error("ffmpeg is not installed or not available in path")
            raise e

        self.punctuations = [".", ";", ":", "!", "?", ","]

        self.cache_dir = Path(self.cfg["cache_dir"])
        self.assets_dir = Path(self.cfg["assets_dir"])

        if "audio" not in self.cfg:
            raise ValueError("Missing 'audio' section in setup.yml")
        self.audio_cfg = self.cfg["audio"]

        if "video" not in self.cfg:
            raise ValueError("Missing 'video' section in setup.yml")
        self.video_cfg = self.cfg["video"]

        # Set up directories
        self.video_dir = self.assets_dir / "background_videos"
        self.music_dir = self.assets_dir / "background_music"
        self.fonts_dir = self.assets_dir / "fonts"
        self.credits_dir = self.assets_dir / "credits"
        # Ensure directories exist
        for directory in [self.video_dir, self.music_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Load audio path
        if audio_path is None:
            self.logger.info(
                f"No audio path provided. Using the audio directory {self.cache_dir} to find an audio file."
            )
            if "output_audio_file" not in self.audio_cfg:
                raise ValueError("Missing 'output_audio_file' in 'audio' section in setup.yml")
            audio_path = self.cache_dir / self.audio_cfg["output_audio_file"]
            self.logger.info(f"Using audio file {audio_path}")
        self.audio_clip: AudioFileClip = AudioFileClip(audio_path)
        self.audio_clip_bitrate = self.audio_clip.reader.bitrate

        if transcript_path is None:
            self.logger.info(
                f"No transcript path provided. Using the audio directory {self.cache_dir} to find a transcript file."
            )
            if "transcript_json" not in self.audio_cfg:
                raise ValueError("Missing 'transcript_json' in 'audio' section in setup.yml")
            transcript_path = self.cache_dir / self.audio_cfg["transcript_json"]
            self.logger.info(f"Using transcript file {transcript_path}")
        # Load the audio transcript
        with open(transcript_path) as audio_transcript_file:
            self.audio_transcript = yaml.safe_load(audio_transcript_file)
        self.audio_transcript: list[dict[str, Any]] = self.preprocess_audio_transcript()
        # Generate Word and sentence transcripts
        self.word_transcript: list[dict[str, Any]] = []
        self.sentences_transcript: list[dict[str, Any]] = []
        self.word_transcript, self.sentences_transcript = (
            self.process_audio_transcript_to_word_and_sentences_transcript()
        )

        if bg_video_path is None:
            self.logger.info(
                "No background video path provided. Using the background_videos_urls to download a background video."
            )
            if "background_videos_urls" not in self.video_cfg:
                raise ValueError("Missing 'background_videos_urls' in 'video' section in setup.yml")
            # choose a random url
            bg_video_url = random.choice(self.video_cfg["background_videos_urls"])
            self.logger.info(f"Using bg_video_url {bg_video_url}")
            bg_videos_path = download_youtube_video(
                bg_video_url,
                self.video_dir,
            )
            bg_video_path = random.choice(bg_videos_path).absolute()
            self.logger.info(f"Using bg_video_path {bg_video_path}")
        self.bg_video: VideoFileClip = VideoFileClip(bg_video_path, audio=False)
        self.bg_video = self.prepare_background_video()
        self.bg_video_bitrate = self.bg_video.reader.bitrate

        if music_path is None:
            self.logger.info(
                "No music path provided. Using the background_music_urls to download a background music."
            )
            if "background_music_urls" not in self.video_cfg:
                raise ValueError("Missing 'background_music_urls' in 'video' section in setup.yml")
            # choose a random url
            music_url = random.choice(self.video_cfg["background_music_urls"])
            self.logger.info(f"Using music_url {music_url}")
            musics_path = download_youtube_music(
                music_url,
                self.music_dir,
            )
            music_path = random.choice(musics_path).absolute()
            self.logger.info(f"Using music_path {music_path}")
        self.music_clip: AudioFileClip = AudioFileClip(music_path)
        self.music_clip_bitrate = self.music_clip.reader.bitrate

        # Get font
        if font_path is None:
            self.logger.info(
                f"No font path provided. Using the fonts directory {self.fonts_dir} to find a font."
            )
            fonts = list(self.fonts_dir.glob("*.ttf"))
            if not fonts:
                raise FileNotFoundError("No font files found in the fonts directory")
            font_path = random.choice(fonts).absolute()
            self.logger.info(f"Using font {font_path}")
        self.font_path = font_path

        # Set the credits
        if credits_path is None:
            self.logger.info(
                f"No credits path provided. Using the credits directory {self.credits_dir} to find a credits file."
            )
            credit_videos = list(self.credits_dir.glob("*.mp4"))
            if not credit_videos:
                raise FileNotFoundError("No credits files found in the credits directory")
            credits_path = self.credits_dir
            self.logger.info(f"Using credits file {credits_path}")

        self.credit_video_mask: VideoFileClip = VideoFileClip(
            credits_path / "credits_mask.mp4", audio=False
        ).to_mask()
        self.credits_video: VideoFileClip = VideoFileClip(
            credits_path / "credits.mp4", audio=False
        ).with_mask(self.credit_video_mask)

        # Set color
        self.color: tuple[int, int, int, int] = colors_dict[random.choice(list(colors_dict.keys()))]
        self.logger.info(f"Using color {self.color}")

        # Create video clips
        self.video_clips: list[VideoFileClip | TextClip] = [self.bg_video]
        self.text_clips: list[TextClip] = []
        self.text_clips = self.create_text_clips()
        self.video_clips.extend(self.text_clips)

    def preprocess_audio_transcript(self) -> list[dict[str, Any]]:
        """Make start of next word the end of the current word."""
        for i in range(len(self.audio_transcript) - 1):
            self.audio_transcript[i]["end"] = self.audio_transcript[i + 1]["start"]
        return self.audio_transcript

    def process_audio_transcript_to_word_and_sentences_transcript(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Process transcript to get word and sentence level information."""

        sentence_start = 0
        sentence_end = 0

        word_start = 0
        word_end = 0

        sentence = ""

        for count, transcript in enumerate(self.audio_transcript):
            word = transcript["word"].strip()
            sentence += word + " "

            word_end = transcript["end"]
            self.word_transcript.append(
                {
                    "word": sentence,
                    "start": word_start,
                    "end": word_end,
                }
            )
            word_start = word_end

            try:
                if word[-1] in self.punctuations and word != "...":
                    sentence_end = word_end
                    self.sentences_transcript.append(
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
            self.sentences_transcript.append(
                {
                    "sentence": sentence,
                    "start": sentence_start,
                    "end": sentence_end,
                }
            )

        return self.word_transcript, self.sentences_transcript

    def prepare_background_video(self) -> VideoFileClip:
        """Prepare the background video with appropriate dimensions and timing."""

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
        """Create text clips for each word in the transcript."""

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
        """Prepare the final audio by combining voice and background music."""

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
        """Generate the final video and save it to the specified output path."""

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
        """Clean up by closing all resources and deleting instance variables."""
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
