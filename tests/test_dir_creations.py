from pathlib import Path


def test_setup_file_exists(setup_file):
    assert setup_file.exists()


def test_dir_creations(setup_file, setup_file_cfg):
    # load yaml file
    cfg = setup_file_cfg
    assert Path(cfg["assets_dir"]).exists()
    assert Path(cfg["cache_dir"]).exists()
