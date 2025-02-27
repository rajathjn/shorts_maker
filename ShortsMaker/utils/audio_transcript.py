import gc
import logging
from pprint import pformat

import torch
import whisperx
from rapidfuzz import process

logger = logging.getLogger(__name__)


def align_transcript_with_script(transcript: list[dict], script_string: str) -> list[dict]:
    """
    Aligns the transcript entries with corresponding segments of a script string by
    comparing text similarities and finding the best matches. This process adjusts
    each transcript entry to align as closely as possible with the correct script
    segment while maintaining the temporal information from the transcript.

    Args:
        transcript (list[dict]): A list of dictionaries, each containing a segment
            of the transcript with keys "text" (text of the segment), "start"
            (start time), and "end" (end time).
        script_string (str): The entire script as a single string to which the
            transcript is aligned.

    Returns:
        list[dict]: A list containing the transcript with updated "text" fields
            that are aligned to the most similar segments of the script. The
            "start" and "end" fields remain unchanged from the input.

    Raises:
        ValueError: If either the transcript or script_string is empty. Applies
            to cases where alignment cannot be performed.

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
    Generates a transcription of an audio file by performing speech-to-text transcription and aligning the
    transcription with a given script. It utilizes whisper models for transcription and alignment to improve
    accuracy.

    This function processes the audio in batches, aligns the transcriptions with the provided script for better
    accuracy, and cleans GPU memory usage during its workflow. It outputs a list of word-level transcriptions
    with start and end times for enhanced downstream processing.

    Args:
        audio_file (str): The path to the audio file that needs to be transcribed.
        script (str): The text script used for alignment with the transcribed segments.
        device (str): The device to be used for computation, default is 'cuda'.
        batch_size (int): The batch size to use during transcription, default is 16.
        compute_type (str): The precision type to be used for the model, default is "float16".
        model (str): The Whisper model variant to use, default is "large-v2". Options include "medium",
            "large-v2", and "large-v3".

    Returns:
        list[dict[str, str | float]]: A list of dictionaries, where each dictionary represents a word in
            the transcription with the word text, start time, and end time.

    Raises:
        Could include potential runtime or memory-related errors specific to the underlying
        libraries or resource management.
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

    logger.debug(
        f"After Alignment:\n {pformat(result['segments'])}"
    )  # before alignment  # after alignment

    word_transcript = []
    for segments in result["segments"]:
        for index, word in enumerate(segments["words"]):
            if "start" not in word:
                word["start"] = segments["words"][index - 1]["end"] if index > 0 else 0
                word["end"] = (
                    segments["words"][index + 1]["start"]
                    if index < len(segments["words"]) - 1
                    else segments["words"][-1]["start"]
                )

            word_transcript.append(
                {"word": word["word"], "start": word["start"], "end": word["end"]}
            )

    logger.debug(f"Transcript:\n {pformat(word_transcript)}")  # before alignment

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    del model_a

    return word_transcript
