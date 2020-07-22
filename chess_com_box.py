from collections import namedtuple
import datetime
import math
import os
import sys
from bs4 import BeautifulSoup
from typing import List
from github.InputFileContent import InputFileContent

import requests
from github import Github

WIDTH_JUSTIFICATION_SEPARATOR = "."
GIST_TITLE = "♟︎ Chess.com Ratings"
MAX_LINE_LENGTH = 52


ENV_VAR_GIST_ID = "GIST_ID"
ENV_VAR_GITHUB_TOKEN = "GH_TOKEN"
ENV_VAR_CHESS_COM_USERNAME = "CHESS_COM_USERNAME"
REQUIRED_ENVS = [
    ENV_VAR_GIST_ID,
    ENV_VAR_GITHUB_TOKEN,
    ENV_VAR_CHESS_COM_USERNAME
]

LIVE_URL_FORMAT = "https://www.chess.com/stats/live/{format}/{user}"
PUZZLES_URL_FORMAT = "https://www.chess.com/stats/{format}/{user}"
DAILY_URL_FORMAT = "https://www.chess.com/stats/{format}/chess/{user}"

TitleAndValue = namedtuple("TitleAndValue", "title value")


def validate_and_init() -> bool:
    env_vars_absent = [
        env
        for env in REQUIRED_ENVS
        if env not in os.environ or len(os.environ[env]) == 0
    ]
    if env_vars_absent:
        print(f"Please define {env_vars_absent} in your github secrets. Aborting...")
        return False

    return True


def get_adjusted_line(title_and_value: TitleAndValue) -> str:
    separation = MAX_LINE_LENGTH - (
        len(title_and_value.title) + len(title_and_value.value) + 2
    )
    separator = f" {WIDTH_JUSTIFICATION_SEPARATOR * separation} "
    return title_and_value.title + separator + title_and_value.value


def scrape_chess_com_rating(rating_url: str) -> str:
    page = requests.get(rating_url, headers = {"Accept-Language": "en-US, en;q=0.5"})
    soup = BeautifulSoup(page.content, 'html.parser')
    rating_div = soup.find('div', 'main-chart-stats-current')
    if rating_div is None:
        return
    return rating_div.text


def get_rating_line(
    chess_url: str, chess_emoji: str, chess_format: str, username: str
) -> TitleAndValue:
    rating = scrape_chess_com_rating(chess_url.format(format=chess_format.lower(), user=username))
    return TitleAndValue(chess_emoji + " " + chess_format, rating + "📈")


def update_gist(title: str, content: str) -> bool:
    access_token = os.environ[ENV_VAR_GITHUB_TOKEN]
    gist_id = os.environ[ENV_VAR_GIST_ID]
    gist = Github(access_token).get_gist(gist_id)
    # Shouldn't necessarily work, keeping for case of single file made in hurry to get gist id.
    old_title = list(gist.files.keys())[0]
    gist.edit(title, {old_title: InputFileContent(content, title)})
    print(f"{title}\n{content}")


def main():

    if not validate_and_init():
        return

    chess_com_user_name = os.environ[ENV_VAR_CHESS_COM_USERNAME]

    blitz_line = get_rating_line(LIVE_URL_FORMAT, "⚡", "Blitz", chess_com_user_name)
    bullet_line = get_rating_line(LIVE_URL_FORMAT, "🚅", "Bullet", chess_com_user_name)
    rapid_line = get_rating_line(LIVE_URL_FORMAT, "⏲️", "Rapid", chess_com_user_name)
    puzzles_line = get_rating_line(PUZZLES_URL_FORMAT, "🧩", "Puzzles", chess_com_user_name)
    daily_line = get_rating_line(DAILY_URL_FORMAT, "☀️", "Daily", chess_com_user_name)

    lines = [
        get_adjusted_line(blitz_line),
        get_adjusted_line(bullet_line),
        get_adjusted_line(rapid_line),
        get_adjusted_line(puzzles_line),
        get_adjusted_line(daily_line)
    ]
    content = "\n".join(lines)
    update_gist(GIST_TITLE, content)


if __name__ == "__main__":
    import time

    s = time.perf_counter()
    # test with python chess_com_box.py test <gist> <github-token> <user>
    if len(sys.argv) > 1:
        os.environ[ENV_VAR_GIST_ID] = sys.argv[2]
        os.environ[ENV_VAR_GITHUB_TOKEN] = sys.argv[3]
        os.environ[ENV_VAR_CHESS_COM_USERNAME] = sys.argv[4]
    main()
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")
