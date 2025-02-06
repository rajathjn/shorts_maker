from pathlib import Path


# Yes, it's dynamic as and depends on the internet and requires you to have valid keys.
def test_get_reddit_post(shorts_maker, setup_file_cfg):
    cfg = setup_file_cfg
    assert shorts_maker.get_reddit_post()
    assert (Path(cfg["cache_dir"]) / cfg["reddit_post_getter"]["record_file_json"]).exists()
    assert (Path(cfg["cache_dir"]) / cfg["reddit_post_getter"]["record_file_txt"]).exists()
