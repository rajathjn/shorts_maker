from pathlib import Path

import yt_dlp

from .logging_config import get_logger

logger = get_logger(__name__)


def download_youtube_music(
    music_url: str, music_dir: Path, force: bool = False
) -> list[Path] | Path:
    """
    Downloads music from a YouTube URL provided, saving it to a specified directory. The method supports
    downloading either the full audio or splitting into chapters, if chapters are available in the video
    metadata. Optionally, existing files can be overwritten if the `force` flag is set.

    Args:
        music_url (str): The YouTube URL of the music video to download.
        music_dir (Path): The directory where the downloaded audio files will be saved.
        force (bool): Specifies whether existing files should be overwritten. Defaults to False.

    Returns:
        list[Path]: A list of paths to the downloaded audio files.
    """
    ydl_opts = {}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        extracted_info = ydl.extract_info(music_url, download=False)
        info_dict = ydl.sanitize_info(extracted_info)

        logger.info(f"Music title: {info_dict['title']}")

        # Handle case with no chapters
        if not info_dict["chapters"]:
            logger.info("No chapters found. Downloading full audio...")
            ydl_opts = {
                "format": "bestaudio",
                "outtmpl": str(music_dir / "%(title)s.%(ext)s"),
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "wav",
                        "preferredquality": "0",
                    }
                ],
                "restrictfilenames": True,
            }
            logger.info(f"Video title: {info_dict['title']}")
            sanitized_filename = ydl.prepare_filename(extracted_info)
            logger.info(f"Sanitized filename will be: {sanitized_filename}")

            output_path = Path(sanitized_filename)
            if (not output_path.exists() and not force) or force:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_audio:
                    ydl_audio.download([music_url])
                    logger.info("Full audio downloaded successfully!")
            return output_path

        # Handle case with chapters
        for chapter in info_dict["chapters"]:
            logger.info(f"Found chapter: {chapter['title']}")
            sanitized_filename = chapter["title"]
            sanitized_filename = sanitized_filename.strip()
            sanitized_filename = sanitized_filename.strip(" .")
            sanitized_filename = sanitized_filename.replace(" ", "_")
            invalid_chars = '<>:"/\\|?*'
            sanitized_filename = "".join(
                "_" if c in invalid_chars else c for c in sanitized_filename
            )

            ydl_opts = {
                "format": "bestaudio",
                "outtmpl": str(music_dir / f"{sanitized_filename}.%(ext)s"),
                "download_ranges": lambda chapter_range, *args: [
                    {
                        "start_time": chapter["start_time"],
                        "end_time": chapter["end_time"],
                        "title": chapter["title"],
                    }
                ],
                "force_keyframes_at_cuts": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "wav",
                        "preferredquality": "0",
                    }
                ],
                "restrictfilenames": True,
            }

            output_path = music_dir / f"{sanitized_filename}.wav"
            logger.info(f"Output path: {output_path.absolute()}")
            if (not output_path.exists() and not force) or force:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_chapter_audio:
                    ydl_chapter_audio.download([music_url])
                    print(f"Chapter downloaded: {chapter['title']}")

    # Return path to first music file found
    music_files = list(music_dir.glob("*.wav"))
    return music_files
