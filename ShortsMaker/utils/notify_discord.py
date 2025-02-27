import json
import os
import textwrap
from random import choice, randint

import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordEmbed, DiscordWebhook
from requests import Response

if not os.environ.get("DISCORD_WEBHOOK_URL"):
    raise ValueError("DISCORD_WEBHOOK_URL not set, Please set it in your environment variables.")

DISCORD_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def get_arthas():
    """
    Fetches a random Arthas image URL from Bing image search results.

    This function sends a search request to Bing images for the keyword 'arthas'
    and retrieves a specific page of the search results. It extracts image URLs
    from the returned HTML content and returns one randomly selected image URL.

    Returns:
        str: A randomly selected URL of an Arthas image.

    Raises:
        requests.exceptions.RequestException: If the HTTP request fails or encounters an issue.
    """
    url = f"https://www.bing.com/images/search?q=arthas&first={randint(1, 10)}"
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) \
                            Chrome/50.0.2661.102 Safari/537.36"
        },
    )
    soup = BeautifulSoup(response.content, "lxml")
    divs = soup.find_all("div", class_="imgpt")
    imgs = []
    for div in divs:
        img = div.find("a")["m"]
        img = img.split("murl")[1].split('"')[2]
        imgs.append(img)
    return choice(imgs)


def get_meme():
    """
    Fetches a meme image URL from the meme-api.com API.

    This function uses the "gimme" endpoint of the meme-api.com to fetch a
    meme image URL. The API allows for specifying a subreddit and quantity
    of meme images. The default behavior is to fetch a random meme from the
    API. The response is parsed and the URL of the image is extracted and
    returned. The function applies a User-Agent header as part of the
    request to prevent potential issues with the API.

    Returns:
        str: The URL of the meme image.

    Raises:
        JSONDecodeError: If the response content could not be decoded into JSON.
        KeyError: If the expected "url" key is not found in the JSON response.
        RequestException: If there is an issue with the HTTP request.

    """
    # Uses https://meme-api.com/gimme/
    # Can use custom subreddit and return multiple images
    # Endpoint: /gimme/{subreddit}/{count}
    # Example: https://meme-api.com/gimme/wholesomememes/2
    # Returns:
    #     Image url
    url = "https://meme-api.com/gimme"
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) \
                            Chrome/50.0.2661.102 Safari/537.36"
        },
    )
    soup = BeautifulSoup(response.content, "html.parser")
    return json.loads(soup.text)["url"]


def notify_discord(message) -> Response:
    """
    Sends a notification message to a Discord webhook, splitting messages longer than the character limit,
    and embedding additional information such as title, description, and images.

    Args:
        message (str): The message content to be sent to the Discord webhook. If the message exceeds 4000
            characters, it will be split into smaller parts.

    Returns:
        Response: The response object resulting from the webhook execution, which contains information
            such as status code and response text.
    """
    messages = textwrap.wrap(message, 4000)
    response = None

    for message in messages:
        webhook = DiscordWebhook(url=DISCORD_URL, rate_limit_retry=True)

        embed = DiscordEmbed()
        embed.set_title(":warning:Error found while running the Automation!:warning:")
        embed.set_description(f"{message}")
        embed.set_image(url=get_meme())
        embed.set_thumbnail(url=get_arthas())
        embed.set_color("ff0000")
        embed.set_timestamp()
        webhook.add_embed(embed)

        response = webhook.execute()
        print(response.status_code)
        print(response.text)
    return response
