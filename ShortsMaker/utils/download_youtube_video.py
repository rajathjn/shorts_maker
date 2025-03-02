from pathlib import Path

import yt_dlp

from .logging_config import get_logger

logger = get_logger(__name__)


def download_youtube_video(video_url: str, video_dir: Path, force: bool = False) -> list[Path]:
    """
    Downloads a YouTube video given its URL and stores it in the specified directory. The
    video is downloaded in the best available MP4 format, and its filename is sanitized to
    remove invalid characters. Provides an option to force download the video even if the
    target file already exists.

    Args:
        video_url: The URL of the video to be downloaded from YouTube.
        video_dir: The directory where the video will be saved.
        force: If True, forces the download even if the video file already exists. Defaults
            to False.

    Returns:
        list[Path]: A list containing the Path objects of the '.mp4' files in the specified
            directory after the download process.
    """
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "outtmpl": str(video_dir / "%(title)s.%(ext)s"),
        "restrictfilenames": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        info_dict = ydl.sanitize_info(info)

        logger.info(f"Video title: {info_dict['title']}")
        sanitized_filename = ydl.prepare_filename(info)
        logger.info(f"Sanitized filename will be: {sanitized_filename}")

        output_path = Path(sanitized_filename)
        if (not output_path.exists() and not force) or force:
            ydl.download([video_url])
            logger.info("Video downloaded successfully!")

        bg_files = list(video_dir.glob("*.mp4"))
        return bg_files
