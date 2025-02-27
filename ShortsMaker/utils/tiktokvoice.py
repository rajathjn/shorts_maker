import base64
import io
import logging
import sys
import textwrap
from threading import Thread

import requests
from pydub import AudioSegment

from .retry import retry

logger = logging.getLogger(__name__)

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
    "en_au_001",  # English AU - Female
    "en_au_002",  # English AU - Male
    "en_uk_001",  # English UK - Male 1
    "en_uk_003",  # English UK - Male 2
    "en_us_001",  # English US - Female (Int. 1)
    "en_us_002",  # English US - Female (Int. 2)
    "en_us_006",  # English US - Male 1
    "en_us_010",  # English US - Male 4
    "en_female_emotional",  # peaceful
]


# define the text-to-speech function
@retry(max_retries=3, delay=5)
def tts(text: str, voice: str, output_filename: str = "output.mp3") -> None:
    """
    Converts provided text into synthesized speech using a given voice. The function splits the input text into chunks,
    sends requests to specific endpoints to generate audio for each chunk, and concatenates the resulting audio into
    a single output file. Each chunk is processed in parallel using threads.

    Args:
        text (str): The text to be converted into speech. Must not be empty.
        voice (str): The voice to be used for text-to-speech synthesis. Must be a valid predefined voice.
        output_filename (str): The filename where the generated audio will be stored. Defaults to "output.mp3".

    Raises:
        ValueError: If the provided `voice` is not a valid voice or the `text` is empty.

    """
    # specified voice is valid
    if voice not in VOICES:
        raise ValueError("voice must be valid")

    # text is not empty
    if not text:
        raise ValueError("text must not be 'None'")

    # split the text into chunks
    chunks: list[str] = _split_text(text)
    logger.info(f"text: {text}")
    logger.info(f"Split text into {len(chunks)} chunks")
    for chunk in chunks:
        logger.info(f"Chunk: {chunk}")

    for entry in ENDPOINT_DATA:
        VALID_ENDPOINT: bool = True
        # empty list to store the data from the requests
        audio_data: list[str] = [""] * len(chunks)

        # generate audio for each chunk in a separate thread
        def generate_audio_chunk(index: int, chunk: str) -> None:
            nonlocal VALID_ENDPOINT
            if not VALID_ENDPOINT:
                return
            try:
                # request to the endpoint to generate audio for the chunk
                response = requests.post(
                    entry["url"],
                    json={"text": chunk, "voice": voice},
                    headers={
                        "User-Agent": "com.zhiliaoapp.musically/2022600030 (Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)",
                    },
                )
                if response.status_code == 200:
                    # store the audio data for the chunk
                    audio_data[index] = response.json()[entry["response"]]
                else:
                    logger.info(f"response: {response}, Endpoint not valid: {entry['url']}")
                    VALID_ENDPOINT = False
            except requests.RequestException as e:
                print(f"Error: {e}")
                sys.exit()
            return

        # start threads for generating audio for each chunk
        threads: list[Thread] = []
        for index, chunk in enumerate(chunks):
            thread: Thread = Thread(target=generate_audio_chunk, args=(index, chunk))
            threads.append(thread)
            thread.start()

        # wait for all threads to finish
        for thread in threads:
            thread.join()

        if not VALID_ENDPOINT:
            continue

        # Assuming audio_data is a list of base64 encoded audio chunks received from the server
        # Concatenate audio data from all chunks and decode from base64
        audio_bytes = b"".join(base64.b64decode(chunk) for chunk in audio_data)
        # Convert the audio bytes to an AudioSegment
        audio_segment: AudioSegment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        # Export the AudioSegment to a file
        audio_segment.export(output_filename, format="wav")
        break


def _split_text(text: str) -> list[str]:
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
    chunk_size: int = 250

    text_list = textwrap.wrap(
        text, width=chunk_size, break_long_words=False, break_on_hyphens=False
    )

    return text_list
