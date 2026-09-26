"""
test_formatter.py
Unit tests for TweetFormatter.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from formatter.tweet_formatter import TweetFormatter

TWITTER_LIMIT = 280

DEFAULT_CONFIG = {
    "tweet": {
        "max_body_lines": 4,
        "hashtags": ["opensource", "devupdate"],
    }
}


@pytest.fixture
def formatter():
    return TweetFormatter(DEFAULT_CONFIG)


def make_release(tag="v1.0.0", name="My App v1.0.0", body="", url=None):
    return {
        "tag_name": tag,
        "name": name,
        "body": body,
        "html_url": url or f"https://github.com/user/repo/releases/tag/{tag}",
    }


# ─────────────────────────────────────────────
# Basic tweet generation
# ─────────────────────────────────────────────

class TestBasicFormatting:
    def test_contains_tag(self, formatter):
        r = make_release(tag="v2.3.0")
        tweet = formatter.format(r)
        assert "v2.3.0" in tweet

    def test_contains_url(self, formatter):
        r = make_release(url="https://github.com/acme/app/releases/tag/v1.0.0")
        tweet = formatter.format(r)
        assert "https://github.com/acme/app/releases/tag/v1.0.0" in tweet

    def test_within_twitter_limit(self, formatter):
        body = "\n".join([f"Feature {i}: some long description here" for i in range(20)])
        r = make_release(body=body)
        tweet = formatter.format(r)
        assert len(tweet) <= TWITTER_LIMIT, f"Tweet too long: {len(tweet)} chars\n{tweet}"

    def test_empty_body_still_produces_tweet(self, formatter):
        r = make_release(body="")
        tweet = formatter.format(r)
        assert len(tweet) > 0
        assert len(tweet) <= TWITTER_LIMIT

    def test_hashtags_present(self, formatter):
        r = make_release()
        tweet = formatter.format(r)
        assert "#opensource" in tweet

    def test_no_hashtags_when_config_empty(self):
        fmt = TweetFormatter({"tweet": {"max_body_lines": 3, "hashtags": []}})
        r = make_release()
        tweet = fmt.format(r)
        assert "#" not in tweet


# ─────────────────────────────────────────────
# Body parsing
# ─────────────────────────────────────────────

class TestBodyParsing:
    def test_fix_lines_classified_separately(self, formatter):
        body = "Added dark mode\nFixed login bug\nImproved speed"
        r = make_release(body=body)
        tweet = formatter.format(r)
        assert "🐛" in tweet  # Fixes section present
        assert "✨" in tweet  # Features section present

    def test_breaking_change_flagged(self, formatter):
        body = "Breaking: removed old API\nAdded new endpoint"
        r = make_release(body=body)
        tweet = formatter.format(r)
        assert "⚠️" in tweet

    def test_feature_lines_appear(self, formatter):
        body = "Added payment integration\nNew dashboard UI"
        r = make_release(body=body)
        tweet = formatter.format(r)
        assert "payment" in tweet.lower() or "dashboard" in tweet.lower()

    def test_max_body_lines_respected(self):
        fmt = TweetFormatter({"tweet": {"max_body_lines": 2, "hashtags": []}})
        body = "\n".join([f"Feature {i}" for i in range(10)])
        r = make_release(body=body)
        tweet = fmt.format(r)
        # Count bullet points
        bullets = [line for line in tweet.splitlines() if line.startswith("•")]
        assert len(bullets) <= 2

    def test_markdown_bullets_stripped(self, formatter):
        body = "- Added search\n* Fixed scroll\n• New icons"
        r = make_release(body=body)
        tweet = formatter.format(r)
        assert "- Added" not in tweet
        assert "* Fixed" not in tweet

    def test_section_headers_skipped(self, formatter):
        body = "## What's New\nAdded dark mode\n## Bug Fixes\nFixed crash"
        r = make_release(body=body)
        tweet = formatter.format(r)
        assert "## What's New" not in tweet


# ─────────────────────────────────────────────
# Edge cases
# ─────────────────────────────────────────────

class TestEdgeCases:
    def test_very_long_single_feature(self, formatter):
        body = "A" * 300
        r = make_release(body=body)
        tweet = formatter.format(r)
        assert len(tweet) <= TWITTER_LIMIT

    def test_name_same_as_tag_not_duplicated(self, formatter):
        r = make_release(tag="v1.0.0", name="v1.0.0")
        tweet = formatter.format(r)
        # Should not contain "(v1.0.0)" since name == tag
        assert "(v1.0.0)" not in tweet

    def test_name_different_from_tag_shows_both(self, formatter):
        r = make_release(tag="v1.0.0", name="Awesome Release")
        tweet = formatter.format(r)
        assert "Awesome Release" in tweet
        assert "v1.0.0" in tweet
