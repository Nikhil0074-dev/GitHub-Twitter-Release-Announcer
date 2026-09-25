"""
GitHub → Twitter Release Announcer
Entry point for the announcement pipeline.
"""

import sys
import os

# Ensure src/ is on the path
sys.path.insert(0, os.path.dirname(__file__))

from github.release_fetcher import ReleaseFetcher
from formatter.tweet_formatter import TweetFormatter
from twitter.twitter_client import TwitterClient
from logger.logger import get_logger
from utils.helpers import load_config, get_env_or_raise

logger = get_logger("main")


def main():
    logger.info("=== GitHub → Twitter Release Announcer Starting ===")

    # Load config
    config = load_config()

    # --- 1. Fetch Release Data ---
    try:
        fetcher = ReleaseFetcher()
        release = fetcher.get_release()
        logger.info(f"Release fetched: {release['tag_name']}")
    except Exception as e:
        logger.error(f"Failed to fetch release data: {e}")
        sys.exit(1)

    # --- 2. Format Tweet ---
    try:
        formatter = TweetFormatter(config)
        tweet_text = formatter.format(release)
        logger.info(f"Tweet formatted ({len(tweet_text)} chars):\n{tweet_text}")
    except Exception as e:
        logger.error(f"Failed to format tweet: {e}")
        sys.exit(1)

    # --- 3. Post Tweet ---
    try:
        client = TwitterClient()
        result = client.post_tweet(tweet_text, release["tag_name"])
        logger.info(f"Tweet posted successfully! Tweet ID: {result['tweet_id']}")
        logger.info(f"Tweet URL: https://twitter.com/i/web/status/{result['tweet_id']}")
    except Exception as e:
        logger.error(f"Failed to post tweet: {e}")
        sys.exit(1)

    logger.info("=== Announcement Complete ===")


if __name__ == "__main__":
    main()
