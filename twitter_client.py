"""
twitter_client.py
Posts tweets via the X (Twitter) API v2 using Tweepy.

Features:
  • OAuth 1.0a authentication (API key + access token)
  • Duplicate tweet prevention via a local state file
  • Exponential-backoff retry on transient failures
  • Returns tweet ID on success
"""

import os
import json
import time
import hashlib
from pathlib import Path

import tweepy

from logger.logger import get_logger

from utils.helpers import get_env_or_raise

logger = get_logger("twitter_client")

# Path for tracking last-posted release (avoids duplicates across runs)
STATE_FILE = Path(__file__).parent.parent.parent / "logs" / "last_posted.json"

MAX_RETRIES = 3
RETRY_BACKOFF = [5, 15, 30]  # seconds between retries


class TwitterClient:
    def __init__(self):
        api_key = get_env_or_raise("TWITTER_API_KEY")
        api_secret = get_env_or_raise("TWITTER_API_SECRET")
        access_token = get_env_or_raise("TWITTER_ACCESS_TOKEN")
        access_secret = get_env_or_raise("TWITTER_ACCESS_SECRET")

        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
        )
        logger.info("Twitter client initialised.")

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def post_tweet(self, text: str, release_tag: str) -> dict:
        """
        Post a tweet, with duplicate-prevention and retry logic.

        Returns:
            {"tweet_id": str}

        Raises:
            RuntimeError if all retries are exhausted.
        """
        # Duplicate guard
        if self._already_posted(release_tag):
            logger.warning(
                f"Release {release_tag} was already announced. Skipping."
            )
            return {"tweet_id": "SKIPPED_DUPLICATE"}

        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Posting tweet (attempt {attempt}/{MAX_RETRIES})…")
                response = self.client.create_tweet(text=text)
                tweet_id = str(response.data["id"])
                self._mark_posted(release_tag, tweet_id)
                return {"tweet_id": tweet_id}

            except tweepy.errors.TooManyRequests as e:
                wait = int(e.response.headers.get("x-rate-limit-reset", time.time() + 60)) - int(time.time())
                wait = max(wait, 10)
                logger.warning(f"Rate limited. Waiting {wait}s before retry…")
                time.sleep(wait)
                last_exc = e

            except tweepy.errors.Forbidden as e:
                # Duplicate tweet content → Twitter returns 403
                logger.error(f"Twitter rejected the tweet (403 Forbidden): {e}")
                raise RuntimeError("Twitter rejected the tweet.") from e

            except tweepy.errors.TweepyException as e:
                logger.warning(f"Tweepy error on attempt {attempt}: {e}")
                last_exc = e
                if attempt < MAX_RETRIES:
                    sleep_time = RETRY_BACKOFF[attempt - 1]
                    logger.info(f"Retrying in {sleep_time}s…")
                    time.sleep(sleep_time)

        raise RuntimeError(
            f"Failed to post tweet after {MAX_RETRIES} attempts. Last error: {last_exc}"
        )

    # ------------------------------------------------------------------
    # Duplicate prevention
    # ------------------------------------------------------------------

    def _load_state(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_state(self, state: dict) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2))

    def _already_posted(self, release_tag: str) -> bool:
        state = self._load_state()
        return release_tag in state.get("posted_releases", [])

    def _mark_posted(self, release_tag: str, tweet_id: str) -> None:
        state = self._load_state()
        posted = state.get("posted_releases", [])
        if release_tag not in posted:
            posted.append(release_tag)
        state["posted_releases"] = posted
        state[release_tag] = {"tweet_id": tweet_id, "timestamp": time.time()}
        self._save_state(state)
        logger.info(f"Marked {release_tag} as posted (tweet_id={tweet_id}).")
