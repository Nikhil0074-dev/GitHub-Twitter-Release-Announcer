"""
test_twitter.py
Tests for TwitterClient — all network calls are mocked.
"""

import sys
import os
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
import tweepy

# Set required env vars before importing the module
os.environ.setdefault("TWITTER_API_KEY", "fake_key")
os.environ.setdefault("TWITTER_API_SECRET", "fake_secret")
os.environ.setdefault("TWITTER_ACCESS_TOKEN", "fake_token")
os.environ.setdefault("TWITTER_ACCESS_SECRET", "fake_access_secret")

from twitter.twitter_client import TwitterClient, STATE_FILE


# ─────────────────────────────────────────────
# Helpers / fixtures
# ─────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_state(tmp_path, monkeypatch):
    """Redirect state file to a temp location and clean up after each test."""
    tmp_state = tmp_path / "last_posted.json"
    monkeypatch.setattr("twitter.twitter_client.STATE_FILE", tmp_state)
    yield tmp_state


@pytest.fixture
def mock_tweepy_client():
    with patch("twitter.twitter_client.tweepy.Client") as MockClient:
        instance = MockClient.return_value
        # Default: successful tweet creation
        instance.create_tweet.return_value = MagicMock(data={"id": "123456789"})
        yield instance


@pytest.fixture
def client(mock_tweepy_client):
    return TwitterClient()


# ─────────────────────────────────────────────
# Successful posting
# ─────────────────────────────────────────────

class TestSuccessfulPosting:
    def test_returns_tweet_id(self, client, mock_tweepy_client):
        result = client.post_tweet("Hello world!", "v1.0.0")
        assert result["tweet_id"] == "123456789"

    def test_create_tweet_called_with_text(self, client, mock_tweepy_client):
        client.post_tweet("My tweet text", "v1.0.0")
        mock_tweepy_client.create_tweet.assert_called_once_with(text="My tweet text")

    def test_state_file_updated_after_post(self, client, mock_tweepy_client, clean_state):
        client.post_tweet("Test tweet", "v2.0.0")
        state = json.loads(clean_state.read_text())
        assert "v2.0.0" in state.get("posted_releases", [])
        assert state["v2.0.0"]["tweet_id"] == "123456789"


# ─────────────────────────────────────────────
# Duplicate prevention
# ─────────────────────────────────────────────

class TestDuplicatePrevention:
    def test_duplicate_release_skipped(self, client, mock_tweepy_client, clean_state):
        # Post once
        client.post_tweet("First tweet", "v1.0.0")
        # Post again with same tag
        result = client.post_tweet("Duplicate tweet", "v1.0.0")
        assert result["tweet_id"] == "SKIPPED_DUPLICATE"
        # create_tweet should only have been called once
        assert mock_tweepy_client.create_tweet.call_count == 1

    def test_different_tags_both_posted(self, client, mock_tweepy_client, clean_state):
        mock_tweepy_client.create_tweet.side_effect = [
            MagicMock(data={"id": "111"}),
            MagicMock(data={"id": "222"}),
        ]
        r1 = client.post_tweet("Tweet 1", "v1.0.0")
        r2 = client.post_tweet("Tweet 2", "v1.1.0")
        assert r1["tweet_id"] == "111"
        assert r2["tweet_id"] == "222"
        assert mock_tweepy_client.create_tweet.call_count == 2


# ─────────────────────────────────────────────
# Retry behaviour
# ─────────────────────────────────────────────

class TestRetryBehaviour:
    def test_retries_on_transient_error(self, client, mock_tweepy_client, clean_state):
        # Fail twice, then succeed
        mock_tweepy_client.create_tweet.side_effect = [
            tweepy.errors.TweepyException("Transient error"),
            tweepy.errors.TweepyException("Transient error"),
            MagicMock(data={"id": "999"}),
        ]
        with patch("twitter.twitter_client.time.sleep"):  # skip real sleep
            result = client.post_tweet("Retried tweet", "v3.0.0")
        assert result["tweet_id"] == "999"
        assert mock_tweepy_client.create_tweet.call_count == 3

    def test_raises_after_max_retries(self, client, mock_tweepy_client, clean_state):
        mock_tweepy_client.create_tweet.side_effect = tweepy.errors.TweepyException("Always fails")
        with patch("twitter.twitter_client.time.sleep"):
            with pytest.raises(RuntimeError, match="Failed to post tweet"):
                client.post_tweet("Failing tweet", "v4.0.0")

    def test_forbidden_raises_immediately(self, client, mock_tweepy_client, clean_state):
        mock_resp = MagicMock()
        mock_tweepy_client.create_tweet.side_effect = tweepy.errors.Forbidden(mock_resp)
        with pytest.raises(RuntimeError, match="Twitter rejected"):
            client.post_tweet("Forbidden tweet", "v5.0.0")
        # Should not retry after Forbidden
        assert mock_tweepy_client.create_tweet.call_count == 1
