from pathlib import Path


def test_generate_audio(shorts_maker, setup_file_cfg):
    cfg = setup_file_cfg
    assert shorts_maker.generate_audio(
        "This is a test to generate audio for the reddit bot. I fucking love you",
        (Path(cfg["cache_dir"]) / "output_test.wav"),
    )
    assert (Path(cfg["cache_dir"]) / "output_test.wav").exists()
    assert (Path(cfg["cache_dir"]) / "generated_audio_script.txt").exists()


def test_generate_audio_with_reddit_post(shorts_maker, setup_file_cfg):
    cfg = setup_file_cfg
    post = shorts_maker.get_reddit_post()
    assert shorts_maker.generate_audio(post)
    assert (Path(cfg["cache_dir"]) / "output.wav").exists()
    assert (Path(cfg["cache_dir"]) / "generated_audio_script.txt").exists()
