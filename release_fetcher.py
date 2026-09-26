"""
release_fetcher.py
Fetches GitHub release data from environment variables (set by GitHub Actions)
or from the GitHub REST API as a fallback.
"""

import os
import requests
from logger.logger import get_logger

logger = get_logger("release_fetcher")


class ReleaseFetcher:
    """
    Retrieves release information for the current GitHub release event.

    Priority:
      1. Environment variables injected by GitHub Actions (fast, no extra API call)
      2. GitHub REST API (fallback / local testing)
    """

    GITHUB_API_BASE = "https://api.github.com"

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repository = os.getenv("GITHUB_REPOSITORY")  # e.g. "owner/repo"
        self.headers = {
            "Accept": "application/vnd.github+json",
            **({"Authorization": f"Bearer {self.token}"} if self.token else {}),
        }

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def get_release(self) -> dict:
        """
        Return a normalised release dict:
          {
            "tag_name": str,
            "name":     str,
            "body":     str,
            "html_url": str,
          }
        """
        release = self._from_env()
        if release:
            logger.info("Release data loaded from environment variables.")
            return release

        logger.info("Env vars not complete – falling back to GitHub API.")
        return self._from_api()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _from_env(self) -> dict | None:
        tag = os.getenv("RELEASE_TAG")
        url = os.getenv("RELEASE_URL")
        body = os.getenv("RELEASE_BODY", "")
        name = os.getenv("RELEASE_NAME", tag or "")

        if tag and url:
            return {
                "tag_name": tag,
                "name": name or tag,
                "body": body,
                "html_url": url,
            }
        return None

    def _from_api(self) -> dict:
        if not self.repository:
            raise ValueError(
                "GITHUB_REPOSITORY env var is required for API fallback. "
                "Set it to 'owner/repo'."
            )

        tag = os.getenv("RELEASE_TAG")

        if tag:
            url = f"{self.GITHUB_API_BASE}/repos/{self.repository}/releases/tags/{tag}"
        else:
            # Get the latest release
            url = f"{self.GITHUB_API_BASE}/repos/{self.repository}/releases/latest"

        logger.info(f"GET {url}")
        response = requests.get(url, headers=self.headers, timeout=15)

        if response.status_code == 404:
            raise ValueError(
                f"Release not found on GitHub. "
                f"Repository: {self.repository}, Tag: {tag or 'latest'}"
            )
        response.raise_for_status()

        data = response.json()
        return {
            "tag_name": data["tag_name"],
            "name": data.get("name") or data["tag_name"],
            "body": data.get("body") or "",
            "html_url": data["html_url"],
        }
