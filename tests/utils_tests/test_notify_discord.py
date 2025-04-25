from unittest.mock import MagicMock, patch

import pytest
from requests import Response

from ShortsMaker.utils.notify_discord import get_arthas, get_meme, notify_discord


@pytest.fixture
def mock_response():
    response = MagicMock(spec=Response)
    response.status_code = 200
    response.text = "Success"
    return response


@pytest.fixture
def mock_webhook():
    with patch("ShortsMaker.utils.notify_discord.DiscordWebhook") as mock:
        webhook = MagicMock()
        webhook.execute.return_value = MagicMock(spec=Response)
        mock.return_value = webhook
        yield mock


@pytest.fixture
def mock_get_meme():
    with patch("ShortsMaker.utils.notify_discord.get_meme") as mock:
        mock.return_value = "http://fake-meme.com/image.jpg"
        yield mock


@pytest.fixture
def mock_get_arthas():
    with patch("ShortsMaker.utils.notify_discord.get_arthas") as mock:
        mock.return_value = "http://fake-arthas.com/image.jpg"
        yield mock


def test_get_arthas(requests_mock):
    mock_html = """
        <div class="imgpt"><a m='{"murl":"test_image.jpg"}'>Test</a></div>
    """
    requests_mock.get("https://www.bing.com/images/search", text=mock_html)
    result = get_arthas()
    assert isinstance(result, str)
    assert result == "test_image.jpg"


def test_get_meme(requests_mock):
    mock_response = {"MemeURL": "http://test-meme.com/image.jpg"}
    requests_mock.get("https://memeapi.zachl.tech/pic/json", json=mock_response)
    result = get_meme()
    assert result == "http://test-meme.com/image.jpg"


def test_notify_discord_short_message(mock_webhook):
    message = "Test message"
    mock_webhook.return_value.execute.return_value = MagicMock(status_code=200)
    result = notify_discord(message)
    mock_webhook.assert_called_once()
    assert result is not None


def test_notify_discord_long_message(mock_webhook, mock_get_meme, mock_get_arthas, mock_response):
    message = "x" * 5000  # Message longer than 4000 chars
    mock_webhook.return_value.execute.return_value = MagicMock(status_code=200)
    result = notify_discord(message)
    assert mock_webhook.call_count > 1
    assert result is not None


@pytest.mark.parametrize(
    "status_code,expected_text",
    [
        (200, "Success"),
        (400, "Bad Request"),
    ],
)
def test_notify_discord_response(
    mock_webhook, mock_get_meme, mock_get_arthas, status_code, expected_text
):
    webhook = mock_webhook.return_value
    response = MagicMock(spec=Response)
    response.status_code = status_code
    response.text = expected_text
    webhook.execute.return_value = response

    result = notify_discord("Test message")
    assert result.status_code == status_code
    assert result.text == expected_text
