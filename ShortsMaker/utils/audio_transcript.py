import gc
import logging
from pprint import pformat

import torch
import whisperx
from rapidfuzz import process

logger = logging.getLogger(__name__)


def align_transcript_with_script(transcript, script_string):
    """
    Aligns transcript text with the best matching portions from the script.

    Args:
        transcript: List of dictionaries with 'start', 'end', and 'text' keys.
        script_string: The original script as a string.

    Returns:
        A list of dictionaries with aligned text, each containing 'text', 'start', and 'end' keys.
    """
    temp_transcript = []
    window_sizes = [i for i in range(6)]
    script_words = script_string.split()

    for entry in transcript:
        possible_windows = []
        length_of_entry_text = len(entry["text"].split())

        # Generate script windows for all specified window sizes
        for window_size in window_sizes:
            possible_windows.extend([" ".join(script_words[: length_of_entry_text + window_size])])
            possible_windows.extend([" ".join(script_words[: length_of_entry_text - window_size])])

        # Find the best match among all possible windows
        # print(f"Entry text: {entry['text']}\n"
        #       f"Possible windows: {possible_windows}"
        #       "\n\n\n"
        #       )
        best_match, score, _ = process.extractOne(entry["text"], possible_windows)

        if best_match:
            script_words = script_words[len(best_match.split()) :]

        # print(
        #     f"Best match: {best_match}, Score: {score} "
        #     f"Script words remaining: {len(script_words)}"
        #     f"Script words: {script_words} \n\n"
        # )

        # Add the match or original text to the new transcript
        temp_transcript.append(
            {
                "text": best_match if best_match else entry["text"],
                "start": entry["start"],
                "end": entry["end"],
            }
        )
    return temp_transcript


def generate_audio_transcription(
    audio_file: str,
    script: str,
    device="cuda",
    batch_size=16,
    compute_type="float16",
    model="large-v2",
) -> list[dict[str, str | float]]:
    """
    Generates the audio file transcription, aligns it with the given script,
    and returns the final aligned transcript.

    Args:
        device: Device to use ("cuda" or "cpu").
        audio_file: Path to the audio file for transcription.
        batch_size: Batch size for transcription.
        compute_type: Compute type ("float16" or "int8").
        script: The script to align the transcript with.
        model: The whisperx model to load.

    Returns:
        list: Word-level transcript as a list of dictionaries with 'word', 'start', and 'end' keys.
    """
    # 1. Transcribe with original whisper (batched)
    # options for models medium, large-v2, large-v3
    model = whisperx.load_model(model, device, compute_type=compute_type)

    audio = whisperx.load_audio(audio_file)
    result = model.transcribe(audio, batch_size=batch_size, language="en")
    logger.debug(f"Before Alignment:\n {pformat(result['segments'])}")  # before alignment

    new_aligned_transcript = align_transcript_with_script(result["segments"], script)

    # delete model if low on GPU resources
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    del model

    # 2. Align whisper output
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(
        new_aligned_transcript,
        model_a,
        metadata,
        audio,
        device,
        return_char_alignments=False,
    )

    logger.debug(f"After Alignment:\n {pformat(result['segments'])}")  # before alignment  # after alignment

    word_transcript = []
    for segments in result["segments"]:
        for index, word in enumerate(segments["words"]):
            if "start" not in word:
                word["start"] = segments["words"][index - 1]["end"] if index > 0 else 0
                word["end"] = segments["words"][index + 1]["start"] if index < len(segments["words"]) - 1 else segments["words"][-1]["start"]

            word_transcript.append({"word": word["word"], "start": word["start"], "end": word["end"]})

    logger.debug(f"Transcript:\n {pformat(word_transcript)}")  # before alignment

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    del model_a

    return word_transcript
