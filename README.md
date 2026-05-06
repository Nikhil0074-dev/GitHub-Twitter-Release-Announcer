
# 🐦 GitHub → Twitter Release Announcer

Automatically posts a tweet on **X (Twitter)** every time you publish a new release on GitHub.

```
New GitHub Release Published
        ↓
GitHub Actions Trigger
        ↓
Fetch Release Data
        ↓
Format Tweet (smart classifier)
        ↓
Post via X API v2   ←── retry + duplicate guard
        ↓
JSON log saved
```

---

## ✨ Features

| Feature | Details |
|---|---|
| **Auto-trigger** | Fires on `release: published` GitHub event |
| **Smart formatting** | Classifies notes into Features / Fixes / Breaking Changes |
| **280-char safety** | Progressively trims content; always fits |
| **Duplicate guard** | Tracks posted releases; skips re-posts |
| **Retry logic** | Exponential backoff on transient API errors |
| **Structured logging** | Colour console + JSON file logs |

---

## 🚀 Quick Start

### 1. Fork / clone this repo

```bash
git clone https://github.com/your-org/github-twitter-announcer.git
cd github-twitter-announcer
```

### 2. Create a Twitter Developer App

1. Go to [developer.twitter.com](https://developer.twitter.com) → **Projects & Apps** → **New App**
2. Set app permissions to **Read and Write**
3. Generate **API Key**, **API Secret**, **Access Token**, **Access Token Secret**

### 3. Add GitHub Secrets

In your GitHub repo → **Settings → Secrets → Actions**, add:

| Secret name | Value |
|---|---|
| `TWITTER_API_KEY` | Your Twitter API key |
| `TWITTER_API_SECRET` | Your Twitter API secret |
| `TWITTER_ACCESS_TOKEN` | Your access token |
| `TWITTER_ACCESS_SECRET` | Your access token secret |

### 4. Publish a release

Go to **Releases → Draft a new release**, fill in the tag and notes, and click **Publish**.  
The workflow fires automatically and posts your tweet. 🎉

---

## 📂 Project Structure

```
github-twitter-announcer/
├── .github/
│   └── workflows/
│       └── announce.yml          # GitHub Actions workflow
├── src/
│   ├── main.py                   # Pipeline entry point
│   ├── github/
│   │   └── release_fetcher.py   # Fetch release from env / API
│   ├── formatter/
│   │   └── tweet_formatter.py   # Format release notes → tweet
│   ├── twitter/
│   │   └── twitter_client.py    # Post tweet with retry + dedup
│   ├── logger/
│   │   └── logger.py            # Console + JSON file logging
│   └── utils/
│       └── helpers.py           # Config loader, env helpers
├── tests/
│   ├── test_formatter.py
│   └── test_twitter.py
├── config/
│   └── config.yaml              # Tweet settings
├── logs/
│   └── app.log                  # Runtime log (gitignored)
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Configuration (`config/config.yaml`)

```yaml
tweet:
  max_body_lines: 4      # Bullet points per section
  hashtags:
    - opensource
    - devupdate
    - github
```

---

## 📝 Tweet Format

Given a release with these notes:

```
Added payment integration
Fixed login crash
Breaking: removed legacy /v1 endpoint
Improved dashboard performance
```

The announcer produces:

```
🚀 New Release: My App (v2.1.0)

⚠️ Breaking Changes:
• Removed legacy /v1 endpoint

✨ What's New:
• Added payment integration
• Improved dashboard performance

🐛 Fixes:
• Fixed login crash

🔗 https://github.com/user/repo/releases/tag/v2.1.0
#opensource #devupdate #github
```

---

## 🧪 Running Tests Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## 🔧 Local Testing

```bash
# Copy and fill in credentials
cp .env.example .env

# Set release vars manually
export RELEASE_TAG=v1.0.0
export RELEASE_URL=https://github.com/you/repo/releases/tag/v1.0.0
export RELEASE_BODY="Added dark mode\nFixed crash on startup"

# Load .env and run
source .env && python src/main.py
```

---

## 🛡️ Security Notes

- API credentials are stored **only** in GitHub Secrets — never in code
- The `.env` file is gitignored; commit only `.env.example`
- `logs/last_posted.json` is gitignored (contains tweet IDs)

---

## 📜 License

MIT
