from pathlib import Path
from unittest.mock import MagicMock, patch


@patch("random.choice")
@patch("praw.Reddit")
def test_get_reddit_post(mock_random_choice, mock_praw_reddit, shorts_maker, setup_file_cfg):
    cfg = setup_file_cfg
    mock_praw_reddit.read_only = True
    mock_praw_reddit.subreddit = MagicMock()
    mock_random_choice.return_value = mock_praw_reddit.subreddit
    mock_praw_reddit.subreddit.title = "test title"
    mock_praw_reddit.subreddit.display_name = "test subreddit"
    mock_praw_reddit.subreddit.top = [{"url": "example.com", "title": "test title"}]
    assert shorts_maker.get_reddit_post()
    assert (Path(cfg["cache_dir"]) / cfg["reddit_post_getter"]["record_file_json"]).exists()
    assert (Path(cfg["cache_dir"]) / cfg["reddit_post_getter"]["record_file_txt"]).exists()
