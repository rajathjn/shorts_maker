import base64
import io
import logging
import sys
import textwrap
from threading import Thread

import requests
from pydub import AudioSegment

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
    # Duplicate voices, so it has more chances to work
    "en_us_001",  # English US - Female (Int. 1)
    "en_us_002",  # English US - Female (Int. 2)
    "en_us_001",  # English US - Female (Int. 1)
    "en_us_002",  # English US - Female (Int. 2)
    "en_us_ghostface",  # Ghost Face
    "en_au_001",  # English AU - Female
    "en_au_002",  # English AU - Male
    "en_uk_001",  # English UK - Male 1
    "en_uk_003",  # English UK - Male 2
    "en_us_001",  # English US - Female (Int. 1)
    "en_us_002",  # English US - Female (Int. 2)
    "en_us_006",  # English US - Male 1
    "en_us_010",  # English US - Male 4
    "en_male_narration",  # narrator
    "en_male_funny",  # wacky
    "en_female_emotional",  # peaceful
]


# define the text-to-speech function
# @retry(max_retries=3, delay=5)
def tts(text: str, voice: str, output_filename: str = "output.mp3") -> None:
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
        endpoint_valid: bool = True

        # empty list to store the data from the requests
        audio_data: list[str] = ["" for i in range(len(chunks))]

        # generate audio for each chunk in a separate thread
        def generate_audio_chunk(index: int, chunk: str) -> None:
            nonlocal endpoint_valid

            if not endpoint_valid:
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
                    logger.info(
                        f"response: {response}, Endpoint not valid: {entry['url']}"
                    )
                    endpoint_valid = False

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

        if not endpoint_valid:
            continue

        # Assuming audio_data is a list of base64 encoded audio chunks received from the server
        # Concatenate audio data from all chunks and decode from base64
        audio_bytes = b"".join(base64.b64decode(chunk) for chunk in audio_data)

        # Convert the audio bytes to an AudioSegment
        audio_segment: AudioSegment = AudioSegment.from_file(io.BytesIO(audio_bytes))

        # Export the AudioSegment to a file
        audio_segment.export(output_filename, format="wav")

        # break after processing a valid endpoint
        break


# define a function to split the text into chunks of maximum 300 characters or less
def _split_text(text: str) -> list[str]:
    # empty list to store merged chunks
    chunk_size: int = 250

    text_list = textwrap.wrap(
        text, width=chunk_size, break_long_words=False, break_on_hyphens=False
    )

    return text_list
