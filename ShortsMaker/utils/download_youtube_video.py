import logging
from pathlib import Path

import yt_dlp

logger = logging.getLogger(__name__)


def download_youtube_video(video_url: str, video_dir: Path, force: bool = False) -> list[Path]:
    """Download background video from URL."""
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
