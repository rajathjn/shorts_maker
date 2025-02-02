from pathlib import Path


def test_get_reddit_post(shorts_maker, setup_file_cfg):
    cfg = setup_file_cfg
    assert shorts_maker.get_reddit_post()
    assert (
        Path(cfg["cache_dir"]) / cfg["reddit_post_getter"]["record_file_json"]
    ).exists()
    assert (
        Path(cfg["cache_dir"]) / cfg["reddit_post_getter"]["record_file_txt"]
    ).exists()
