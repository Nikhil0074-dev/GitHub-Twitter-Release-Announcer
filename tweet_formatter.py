"""
tweet_formatter.py
Converts raw GitHub release data into a well-structured, emoji-enhanced tweet.

Tweet anatomy
─────────────
🚀 New Release: {name} ({tag})

✨ Highlights:
• …
• …

🐛 Fixes:
• …

🔗 {url}

#{hashtags}
"""

import re
import textwrap
from logger.logger import get_logger

logger = get_logger("tweet_formatter")

TWITTER_LIMIT = 280

# Keywords that signal a bug-fix line
FIX_KEYWORDS = re.compile(
    r"\b(fix|bug|patch|resolve|hotfix|correct|repair|revert)\b",
    re.IGNORECASE,
)

# Keywords that signal a breaking change
BREAKING_KEYWORDS = re.compile(
    r"\b(breaking|removed|deprecated|incompatible|migration)\b",
    re.IGNORECASE,
)


class TweetFormatter:
    def __init__(self, config: dict):
        self.max_body_lines: int = config.get("tweet", {}).get("max_body_lines", 5)
        self.hashtags: list[str] = config.get("tweet", {}).get(
            "hashtags", ["opensource", "devupdate"]
        )

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def format(self, release: dict) -> str:
        """
        Return a tweet string ≤ 280 characters.
        Falls back to a minimal template if the full version is too long.
        """
        tag = release["tag_name"]
        name = release.get("name") or tag
        url = release["html_url"]
        body = release.get("body") or ""

        features, fixes, breaking = self._parse_body(body)

        tweet = self._build_tweet(tag, name, url, features, fixes, breaking)

        if len(tweet) > TWITTER_LIMIT:
            logger.warning(
                f"Full tweet ({len(tweet)} chars) exceeds limit; trimming body."
            )
            tweet = self._trim_to_limit(tag, name, url, features, fixes, breaking)

        if len(tweet) > TWITTER_LIMIT:
            tweet = self._minimal_tweet(tag, name, url)

        return tweet

    # ------------------------------------------------------------------
    # Private – parsing
    # ------------------------------------------------------------------

    def _parse_body(self, body: str) -> tuple[list[str], list[str], list[str]]:
        """Classify release-note lines into features / fixes / breaking."""
        features: list[str] = []
        fixes: list[str] = []
        breaking: list[str] = []

        for raw_line in body.splitlines():
            line = raw_line.strip().lstrip("-*•·").strip()
            if not line or line.startswith("#"):
                continue

            if BREAKING_KEYWORDS.search(line):
                breaking.append(self._cap(line))
            elif FIX_KEYWORDS.search(line):
                fixes.append(self._cap(line))
            else:
                features.append(self._cap(line))

        return features, fixes, breaking

    # ------------------------------------------------------------------
    # Private – building
    # ------------------------------------------------------------------

    def _build_tweet(
        self,
        tag: str,
        name: str,
        url: str,
        features: list[str],
        fixes: list[str],
        breaking: list[str],
    ) -> str:
        parts: list[str] = []

        # Header
        header = f"🚀 New Release: {name}"
        if name != tag:
            header += f" ({tag})"
        parts.append(header)

        # Breaking changes (always first if present)
        if breaking:
            parts.append("\n⚠️ Breaking Changes:")
            for item in breaking[: self.max_body_lines]:
                parts.append(f"• {item}")

        # Features
        if features:
            parts.append("\n✨ What's New:")
            for item in features[: self.max_body_lines]:
                parts.append(f"• {item}")

        # Fixes
        if fixes:
            parts.append("\n🐛 Fixes:")
            for item in fixes[: self.max_body_lines]:
                parts.append(f"• {item}")

        # Fallback when notes are empty
        if not features and not fixes and not breaking:
            parts.append("\n📦 A new version is available — see the release notes for details.")

        # Footer
        parts.append(f"\n🔗 {url}")

        if self.hashtags:
            tag_line = " ".join(f"#{h}" for h in self.hashtags)
            parts.append(tag_line)

        return "\n".join(parts)

    def _trim_to_limit(
        self,
        tag: str,
        name: str,
        url: str,
        features: list[str],
        fixes: list[str],
        breaking: list[str],
    ) -> str:
        """Progressively reduce content until it fits."""
        for max_items in range(min(self.max_body_lines, 4), 0, -1):
            tweet = self._build_tweet(
                tag,
                name,
                url,
                features[:max_items],
                fixes[:max_items],
                breaking[:max_items],
            )
            if len(tweet) <= TWITTER_LIMIT:
                return tweet
        return self._minimal_tweet(tag, name, url)

    def _minimal_tweet(self, tag: str, name: str, url: str) -> str:
        header = f"🚀 New Release: {name}"
        if name != tag:
            header += f" ({tag})"
        tweet = f"{header}\n\n🔗 {url}"
        # Append hashtags only if they fit
        if self.hashtags:
            tag_line = " ".join(f"#{h}" for h in self.hashtags)
            candidate = f"{tweet}\n{tag_line}"
            if len(candidate) <= TWITTER_LIMIT:
                return candidate
        return tweet

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _cap(s: str) -> str:
        return s[:1].upper() + s[1:] if s else s
