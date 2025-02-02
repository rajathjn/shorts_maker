from pathlib import Path

from ShortsMaker import ShortsMaker


def test_setup_file_exists(setup_file):
    assert setup_file.exists()


def test_dir_creations(setup_file, setup_file_cfg):
    ShortsMaker(setup_file)
    # load yaml file
    cfg = setup_file_cfg
    assert Path(cfg["assets_dir"]).exists()
    assert Path(cfg["cache_dir"]).exists()
