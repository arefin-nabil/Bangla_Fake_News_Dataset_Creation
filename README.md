# 📰 Bangla Fake News Dataset — Complete Beginner Guide

This project collects Bangla news data from websites and YouTube channels
to build a dataset for a **Fake News Detection** deep learning project.

---

## 📁 What Files Are In This Project?

```
Web_Scraping/
│
├── scraper.py           ← Collects text from news WEBSITES
├── youtube_scraper.py   ← Collects info from YouTube CHANNELS
├── merge.py             ← Merges two CSV files from you + friend
├── requirements.txt     ← List of Python packages needed
├── .gitignore           ← Tells GitHub what NOT to upload
└── README.md            ← This guide
│
│   The files below are AUTO-CREATED when you run the scripts:
│   (They are NOT uploaded to GitHub — see .gitignore)
│
├── news_dataset.csv     ← Your final collected data ⭐
├── visited_urls.txt     ← Remembers which news articles were collected
├── youtube_visited.txt  ← Remembers which YouTube videos were collected
├── last_run_state.json  ← Remembers scraping progress
├── scraper.log          ← News scraper activity log
└── youtube_scraper.log  ← YouTube scraper activity log
```

> ✅ You only ever edit: `scraper.py` and `youtube_scraper.py`
> Everything else is created automatically when you run the scripts.

---

## 📊 CSV Output Format

Both scripts write to the **same file** `news_dataset.csv`:

| Column | Description | Example |
|--------|-------------|---------|
| `id` | Auto number | 1, 2, 3... |
| `title` | Headline / Video title | "বাংলাদেশে ভূমিকম্প" |
| `text` | Article body / Video description | "আজ সকালে..." |
| `source` | Website / Channel name | "Prothom Alo" |
| `publish_date` | Publication date | 2024-03-15 |
| `category` | Content type | national, satire, news |
| `label` | **real** or **fake** | fake |
| `url` | Original link | https://... |
| `content_hash` | Duplicate fingerprint | a3f9c1b2... |

---

## ⚙️ How Much Data Will It Collect?

**News Scraper (scraper.py)** — balanced, 300 per source:

| Source | Label | Max |
|--------|-------|-----|
| Prothom Alo | real | 300 |
| Samakal | real | 300 |
| Naya Diganta | real | 300 |
| BD Pratidin | real | 300 |
| Jugantor | real | 300 |
| Ittefaq | real | 300 |
| Amar Desh | real | 300 |
| Shomoyeralo | real | 300 |
| Daily Inqilab | real | 300 |
| Bonik Barta | real | 300 |
| Earki Humor | **fake** | 300 |
| Earki Satire | **fake** | 300 |
| Earki News | **fake** | 300 |
| Earki Interview | **fake** | 300 |
| **TOTAL** | | **~4,200** |

> Each source stops at its own cap — no single source can dominate the dataset.

---

## 🚀 SETUP — Do This Once

### Step 1 — Install Python
1. Go to → **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python 3.x.x"** button
3. Run the installer
4. ⚠️ **IMPORTANT:** Check the box **"Add Python to PATH"** before clicking Install!

**Verify it worked:**
```
python --version
```
Should show: `Python 3.x.x`

---

### Step 2 — Open Terminal in Project Folder

1. Open your `Web_Scraping` folder in File Explorer
2. Click the address bar at the top
3. Type `powershell` → press Enter
4. A blue PowerShell window opens ✅

---

### Step 3 — Install Required Packages

```powershell
pip install -r requirements.txt
```

---

### Step 4 — Get a FREE YouTube API Key (for YouTube scraper only)

**Takes about 3 minutes:**

1. Go to → **https://console.cloud.google.com/**
2. Sign in with your Google/Gmail account
3. Click the project dropdown at the top → **"NEW PROJECT"** → name it anything → **CREATE**
4. In the search bar, type: `YouTube Data API v3` → click on it → click **ENABLE**
5. In the left sidebar click **Credentials** → **+ CREATE CREDENTIALS** → **API key**
6. Copy the key that appears (looks like: `AIzaSyXXXXXXXXXXX`)
7. Click **CLOSE**

**Add it to the script:**

Open `youtube_scraper.py`, find line ~33:
```python
API_KEY = os.environ.get("YOUTUBE_API_KEY", "YOUR_API_KEY_HERE")
```
Replace `YOUR_API_KEY_HERE` with your actual key:
```python
API_KEY = os.environ.get("YOUTUBE_API_KEY", "AIzaSyXXXXXXXXXXX")
```
> Keep the quote marks `" "` around the key!

---

### Step 5 — Add Your YouTube Channels

Open `youtube_scraper.py`, find the `CHANNELS = [` section and add your channels:

```python
CHANNELS = [
    {
        "url":      "https://www.youtube.com/@YourFakeChannel",
        "label":    "fake",
        "category": "satire",
    },
    {
        "url":      "https://www.youtube.com/@somoynews360",
        "label":    "real",
        "category": "news",
    },
    # Add more channels here...
]
```

Supports any URL format:
- `https://www.youtube.com/@Handle`
- `https://www.youtube.com/channel/UCxxxxxxxx`

---

## ▶️ HOW TO RUN

### Collect news articles (no API key needed):
```powershell
python scraper.py
```

### Collect YouTube videos (needs API key + channels configured):
```powershell
python youtube_scraper.py
```

Both scripts write to the **same** `news_dataset.csv` file automatically.

---

## 🆕 FRESH START — Start Collection From Zero

> ⚠️ Use this if you want to delete ALL existing data and start again from scratch.

### Option 1 — Use the built-in flag:
```powershell
python scraper.py --fresh
python youtube_scraper.py --fresh
```
This deletes `visited_urls.txt`, `last_run_state.json` (for news scraper) or `youtube_visited.txt` (for YouTube scraper) before starting. **The CSV file is also deleted** so you start with empty data.

### Option 2 — Delete files manually:

Delete these files from the folder (just delete them in File Explorer):
```
news_dataset.csv       ← your collected data (WILL BE LOST)
visited_urls.txt       ← news scraper memory
youtube_visited.txt    ← youtube scraper memory
last_run_state.json    ← scraper progress tracker
scraper.log            ← log file (safe to delete)
youtube_scraper.log    ← log file (safe to delete)
```
Then run the scripts normally.

> ⚠️ **WARNING:** Fresh start means losing ALL previously collected data.
> Only do this if you are sure you want to start over!
> If you just want to collect MORE data, run the script normally — it resumes automatically.

---

## ⏸️ Stopping & Resuming (NO data loss)

- Press **Ctrl + C** to stop anytime
- Run the same command again to **resume from where you stopped**
- No duplicates will be added — the script remembers everything

---

## 📊 Watching Progress

While the script runs, you'll see output like:
```
[1/4200] (real) [Prothom Alo] সংসদে বাজেট অনুমোদন...
[2/4200] (fake) [Earki Humor] ঢাকায় বৃষ্টির কারণে সকল মানুষ মাছ...
✋ [Prothom Alo] cap of 300 reached — moving on
💾 Batch saved | total_new=10
```

- `✋ cap reached` → that source hit its 300 limit, moving to next source
- `💾 Batch saved` → data saved to CSV (happens every 10 articles)

---

## 🔧 Changing the Collection Limit

**Change how many articles each source collects:**

In `scraper.py`, find any source and change its `"max"` value:
```python
{
    "name": "Prothom Alo",
    "max":  500,          # ← change this number
    ...
}
```

**Or override ALL sources at runtime:**
```powershell
python scraper.py --per_source 500
```
This sets every source to collect 500 articles this run.

---

## 👥 SHARING WITH A FRIEND

### Upload to GitHub (recommended)

**Install Git:** https://git-scm.com/downloads

```powershell
git init
git add scraper.py youtube_scraper.py merge.py requirements.txt .gitignore README.md
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

> The `.gitignore` file automatically prevents CSV data, logs, and API keys from being uploaded.

### Your friend clones it:
```powershell
git clone https://github.com/YOUR_USERNAME/REPO_NAME.git
cd REPO_NAME
pip install -r requirements.txt
```

Then they:
- Add their own YouTube API key to `youtube_scraper.py`
- Add YouTube channels to the `CHANNELS` list
- Run the scripts normally

### Merging both datasets:

1. Share `news_dataset.csv` files (use Google Drive — can be large)
2. Rename them: `my_data.csv` and `friends_data.csv`
3. Edit `merge.py` and update the file names at the top
4. Run:
```powershell
python merge.py
```
Output: `merged_final.csv` with all duplicates removed automatically.

---

## 🔴 Common Problems & Fixes

| Problem | Fix |
|---------|-----|
| `python: command not found` | Reinstall Python, check "Add to PATH" |
| `pip: command not found` | Use `python -m pip install -r requirements.txt` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| `API key not set` error | Add your API key to `youtube_scraper.py` Step 4 |
| `quotaExceeded` YouTube error | Daily limit hit — come back tomorrow |
| Script is very slow | Normal! It sleeps between requests to avoid being blocked |
| `news_dataset.csv` is empty | Wait a few minutes — some sites take time |

---

## 📞 Quick Command Reference

```powershell
# Collect news articles (300 per source, balanced)
python scraper.py

# Collect YouTube videos
python youtube_scraper.py

# Fresh start — delete all old data
python scraper.py --fresh
python youtube_scraper.py --fresh

# Custom limits
python scraper.py --per_source 500
python youtube_scraper.py --max 1000

# Merge your data + friend's data
python merge.py
```
