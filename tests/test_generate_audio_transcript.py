from pathlib import Path


def test_generate_audio_transcript(shorts_maker, setup_file_cfg):
    cfg = setup_file_cfg
    assert (Path(cfg["cache_dir"]) / "output.wav").exists()
    assert (Path(cfg["cache_dir"]) / "generated_audio_script.txt").exists()
    assert shorts_maker.generate_audio_transcript(
        Path(cfg["cache_dir"]) / "output.wav",
        Path(cfg["cache_dir"]) / "generated_audio_script.txt",
        Path(cfg["cache_dir"]) / "transcript.json",
    )
    assert (Path(cfg["cache_dir"]) / "transcript.json").exists()
