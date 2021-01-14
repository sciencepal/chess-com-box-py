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

ENV_VAR_GIST_ID = "GIST_ID"
ENV_VAR_GITHUB_TOKEN = "GH_TOKEN"
ENV_VAR_CHESS_COM_USERNAME = "CHESS_COM_USERNAME"
REQUIRED_ENVS = [
    ENV_VAR_GIST_ID,
    ENV_VAR_GITHUB_TOKEN,
    ENV_VAR_CHESS_COM_USERNAME
]

# LIVE_URL_FORMAT = "https://www.chess.com/stats/live/{format}/{user}"
# PUZZLES_URL_FORMAT = "https://www.chess.com/stats/{format}/{user}"
# DAILY_URL_FORMAT = "https://www.chess.com/stats/{format}/chess/{user}"
STATS_URL = "https://api.chess.com/pub/player/{user}/stats"

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


def get_adjusted_line(title_and_value: TitleAndValue, max_line_length: int) -> str:
    separation = max_line_length - (
        len(title_and_value.title) + len(title_and_value.value) + 2
    )
    separator = f" {WIDTH_JUSTIFICATION_SEPARATOR * separation} "
    return title_and_value.title + separator + title_and_value.value


def get_chess_com_stats(user: str = "sciencepal") -> dict:
    stats_dict = requests.get(STATS_URL.format(user=user)).json()
    return stats_dict


def get_rating_line(
    stats_key: str, chess_emoji: str, chess_format: str, chess_stats: dict
) -> TitleAndValue:
    try:
        rating = str(chess_stats.get(stats_key).get("highest" if (chess_format == "Tactics") else "last").get("rating"))
    except Exception as e:
        rating = "N/A"
    return TitleAndValue(chess_emoji + " " + chess_format, rating + " 📈")


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
    chess_stats = get_chess_com_stats(chess_com_user_name)

    blitz_line = get_rating_line("chess_blitz", "⚡", "Blitz", chess_stats)
    bullet_line = get_rating_line("chess_bullet", "🚅", "Bullet", chess_stats)
    rapid_line = get_rating_line("chess_rapid", "⏲️", "Rapid", chess_stats)
    puzzles_line = get_rating_line("tactics", "🧩", "Tactics", chess_stats)
    daily_line = get_rating_line("chess_daily", "☀️", "Daily", chess_stats)

    lines = [
        get_adjusted_line(blitz_line, 52),
        get_adjusted_line(bullet_line, 52),
        get_adjusted_line(rapid_line, 53),
        get_adjusted_line(puzzles_line, 52),
        get_adjusted_line(daily_line, 53)
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
