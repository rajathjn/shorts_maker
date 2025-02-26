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
    Scraps the search query for Arthas image
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
    Uses https://meme-api.com/gimme/
    Can use custom subreddit and return multiple images
    Endpoint: /gimme/{subreddit}/{count}
    Example: https://meme-api.com/gimme/wholesomememes/2
    Returns:
        Image url
    """
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
    Notify Discord channel
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
