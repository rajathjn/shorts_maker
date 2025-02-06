import json
import tempfile
from pathlib import Path


def test_generate_audio_transcript(shorts_maker):
    temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_audio = Path(temp_audio.name)
    temp_json = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    temp_json = Path(temp_json.name)
    try:
        assert shorts_maker.generate_audio(
            "This is a test to generate audio for the reddit bot.",
            temp_audio,
        )
        assert (temp_audio.parent / "generated_audio_script.txt").exists()
        assert shorts_maker.generate_audio_transcript(
            temp_audio,
            temp_audio.parent / "generated_audio_script.txt",
            temp_json,
        )
        temp_text_in_json_value = [
            {"word": "This"},
            {"word": "is"},
            {"word": "a"},
            {"word": "test"},
            {"word": "to"},
            {"word": "generate"},
            {"word": "audio"},
            {"word": "for"},
            {"word": "the"},
            {"word": "reddit"},
            {"word": "bot."},
        ]
        function_json_value = json.load(temp_json.open())
        assert [i["word"] for i in function_json_value] == [i["word"] for i in temp_text_in_json_value]
    finally:
        assert temp_audio.exists()
        temp_audio.unlink()
        assert temp_json.exists()
        temp_json.unlink()


def test_generate_audio_transcript_with_reddit_post(shorts_maker, setup_file_cfg):
    cfg = setup_file_cfg
    assert (Path(cfg["cache_dir"]) / "output.wav").exists()
    assert (Path(cfg["cache_dir"]) / "generated_audio_script.txt").exists()
    assert shorts_maker.generate_audio_transcript(
        Path(cfg["cache_dir"]) / "output.wav",
        Path(cfg["cache_dir"]) / "generated_audio_script.txt",
        Path(cfg["cache_dir"]) / "transcript.json",
    )
    assert (Path(cfg["cache_dir"]) / "transcript.json").exists()
