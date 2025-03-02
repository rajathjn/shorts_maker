from .audio_transcript import align_transcript_with_script, generate_audio_transcription
from .colors_dict import COLORS_DICT
from .download_youtube_music import download_youtube_music
from .download_youtube_video import download_youtube_video
from .get_tts import VOICES, tts
from .logging_config import configure_logging, get_logger
from .notify_discord import notify_discord
from .retry import retry

__all__ = [
    align_transcript_with_script,
    configure_logging,
    download_youtube_music,
    download_youtube_video,
    generate_audio_transcription,
    get_logger,
    notify_discord,
    retry,
    tts,
    COLORS_DICT,
    VOICES,
]

# Configure logging to their preferences
configure_logging()
