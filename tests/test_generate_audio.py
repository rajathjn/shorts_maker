import tempfile
from pathlib import Path


def test_generate_audio(shorts_maker):
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_file = Path(temp_file.name)
    try:
        assert shorts_maker.generate_audio(
            "This is a test to generate audio for the reddit bot.",
            temp_file,
        )
        assert (temp_file.parent / "generated_audio_script.txt").exists()
    finally:
        assert temp_file.exists()
        temp_file.unlink()


def test_generate_audio_with_reddit_post(shorts_maker, setup_file_cfg):
    cfg = setup_file_cfg
    post = shorts_maker.get_reddit_post()
    assert shorts_maker.generate_audio(post)
    assert (Path(cfg["cache_dir"]) / "output.wav").exists()
    assert (Path(cfg["cache_dir"]) / "generated_audio_script.txt").exists()
