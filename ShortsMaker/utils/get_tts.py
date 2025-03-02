import base64
import io
import sys
import textwrap
from threading import Thread

import requests
from pydub import AudioSegment

from .logging_config import get_logger
from .retry import retry

logger = get_logger(__name__)

# define the endpoint data with URLs and corresponding response keys
ENDPOINT_DATA = [
    {
        "url": "https://tiktok-tts.weilnet.workers.dev/api/generation",
        "response": "data",
    },
    {"url": "https://countik.com/api/text/speech", "response": "v_data"},
    {"url": "https://gesserit.co/api/tiktok-tts", "response": "base64"},
]

# define available voices for text-to-speech conversion
VOICES = [
    "en_us_001",  # English US - Female (Int. 1)
    "en_us_002",  # English US - Female (Int. 2)
    "en_au_002",  # English AU - Male
    "en_uk_001",  # English UK - Male 1
    "en_uk_003",  # English UK - Male 2
    "en_us_006",  # English US - Male 1
    "en_us_010",  # English US - Male 4
    "en_female_emotional",  # peaceful
]


# define the text-to-speech function
@retry(max_retries=3, delay=5)
def tts(text: str, voice: str, output_filename: str = "output.mp3") -> None:
    """
    Converts text to speech using specified voice and saves to output file.

    Args:
        text (str): Input text to convert
        voice (str): Voice ID to use
        output_filename (str): Output audio file path

    Raises:
        ValueError: If voice is invalid or text is empty
    """
    _validate_inputs(text, voice)
    chunks = _split_text(text)
    _log_chunks(text, chunks)

    global ENDPOINT_DATA

    audio_data = [""] * len(chunks)
    for endpoint in ENDPOINT_DATA:
        audio_data = _process_chunks(chunks, endpoint, voice, audio_data)
        if audio_data is not None:
            _save_audio(audio_data, output_filename)
            break


def _validate_inputs(text: str, voice: str) -> None:
    if voice not in VOICES:
        raise ValueError("voice must be valid")
    if not text:
        raise ValueError("text must not be 'None'")


def _log_chunks(text: str, chunks: list[str]) -> None:
    logger.info(f"text: {text}")
    logger.info(f"Split text into {len(chunks)} chunks")
    for chunk in chunks:
        logger.info(f"Chunk: {chunk}")


def _process_chunks(
    chunks: list[str], endpoint: dict, voice: str, audio_data: list[str]
) -> list[str] | None:
    valid = True

    def generate_audio_chunk(index: int, chunk: str) -> None:
        nonlocal valid
        if not valid:
            return

        try:
            response = requests.post(
                endpoint["url"],
                json={"text": chunk, "voice": voice},
                headers={
                    "User-Agent": "com.zhiliaoapp.musically/2022600030 (Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)",
                },
            )
            if response.status_code == 200:
                audio_data[index] = response.json()[endpoint["response"]]
            else:
                logger.info(f"response: {response}, Endpoint not valid: {endpoint['url']}")
                valid = False
        except requests.RequestException as e:
            print(f"Error: {e}")
            sys.exit()

    threads = [
        Thread(target=generate_audio_chunk, args=(i, chunk)) for i, chunk in enumerate(chunks)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    return audio_data if valid else None


def _save_audio(audio_data: list[str], output_filename: str) -> None:
    audio_bytes = b"".join(base64.b64decode(chunk) for chunk in audio_data)
    audio_segment: AudioSegment = AudioSegment.from_file(io.BytesIO(audio_bytes))
    audio_segment.export(output_filename, format="wav")


def _split_text(text: str, chunk_size: int = 250) -> list[str]:
    """
    Splits a given text into smaller chunks of a specified size without breaking
    words or splitting on hyphens.

    The function wraps the input text into smaller substrings, ensuring the
    integrity of the text by preventing cutoff mid-word or mid-hyphen. Each chunk
    is at most of the specified chunk size.

    Args:
        text (str): The input text to be split into smaller chunks.

    Returns:
        list[str]: A list of text chunks where each chunk is at most the
        specified size while preserving word integrity.
    """

    text_list = textwrap.wrap(
        text, width=chunk_size, break_long_words=False, break_on_hyphens=False
    )

    return text_list
