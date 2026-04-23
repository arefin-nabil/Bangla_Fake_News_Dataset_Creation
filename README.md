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
├── requirements.txt     ← List of tools Python needs to install
├── README.md            ← This guide file
│
│── The files below are AUTO-CREATED when you run the scripts:
├── news_dataset.csv     ← Your final collected data (the important one!)
├── visited_urls.txt     ← Remembers which websites were already collected
├── youtube_visited.txt  ← Remembers which YouTube videos were already collected
├── last_run_state.json  ← Remembers scraping progress
├── scraper.log          ← Activity log of news scraper
└── youtube_scraper.log  ← Activity log of YouTube scraper
```

> ✅ You only need to touch: `scraper.py`, `youtube_scraper.py`
> Everything else is created automatically.

---

## 🖥️ STEP 1 — Install Python (Skip if already installed)

1. Go to → **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python 3.x.x"** button
3. Run the downloaded installer
4. ⚠️ **VERY IMPORTANT:** Before clicking Install, check the box that says:
   > ✅ **"Add Python to PATH"**
   
   If you miss this, Python won't work in the terminal!
5. Click **Install Now** and wait

**How to check if Python is installed correctly:**
- Press `Windows Key + R` → type `cmd` → press Enter
- Type this and press Enter:
  ```
  python --version
  ```
- You should see something like: `Python 3.12.0`
- If you see an error, Python wasn't installed correctly — try again

---

## 🖥️ STEP 2 — Open the Terminal IN the Project Folder

You need to open the terminal (command prompt / PowerShell) **inside** your project folder.

**Easy way:**
1. Open your `Web_Scraping` folder in File Explorer
2. Click on the address bar at the top (where it shows the folder path)
3. Type `powershell` and press **Enter**
4. A blue PowerShell window will open already in the right folder ✅

---

## 📦 STEP 3 — Install Required Packages (Do This Once)

In the PowerShell window you just opened, type this exactly and press Enter:

```
pip install -r requirements.txt
```

You'll see it downloading and installing packages. Wait until it says done.

If `pip` doesn't work, try:
```
python -m pip install -r requirements.txt
```

---

## 🔑 STEP 4 — Get Your FREE YouTube API Key

> ⚠️ You need this ONLY for `youtube_scraper.py`. Skip this if you're only using `scraper.py`.

This takes about **3–5 minutes**. Follow carefully:

### 4A — Go to Google Cloud Console
1. Open your browser and go to → **https://console.cloud.google.com/**
2. Sign in with your **Google account** (Gmail works)

### 4B — Create a New Project
1. At the very top of the page, click on the **project dropdown** (it says "Select a project" or shows a project name)
2. Click **"NEW PROJECT"** in the top right of the popup
3. Give it any name, like: `fake-news-scraper`
4. Click **"CREATE"** and wait a few seconds
5. Make sure your new project is selected (shown at the top)

### 4C — Enable YouTube API
1. In the search bar at the top, type: `YouTube Data API v3`
2. Click on **"YouTube Data API v3"** from the results
3. Click the big blue **"ENABLE"** button
4. Wait for it to enable (a few seconds)

### 4D — Create Your API Key
1. On the left sidebar, click **"Credentials"**
   - If you don't see the sidebar, click the ☰ (hamburger menu) at the top left
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"API key"** from the dropdown
4. A popup will appear showing your API key — it looks like:
   ```
   AIzaSyD_xxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
5. Click the **copy icon** to copy it
6. Click **"CLOSE"**

> ✅ That's your YouTube API Key! Keep it safe — don't share it publicly.

---

## ✏️ STEP 5 — Add Your API Key to the Script

1. Open `youtube_scraper.py` in any text editor
   - VS Code (recommended), Notepad, Notepad++ — anything works
2. Find this line near the top (around line 33):
   ```python
   API_KEY = os.environ.get("YOUTUBE_API_KEY", "YOUR_API_KEY_HERE")
   ```
3. Replace `YOUR_API_KEY_HERE` with your actual key:
   ```python
   API_KEY = os.environ.get("YOUTUBE_API_KEY", "AIzaSyD_xxxxxxxxxxxxxxxxxxxxxxxxxxx")
   ```
   > ⚠️ Keep the quotes `" "` around your key!

---

## 📺 STEP 6 — Add Your YouTube Channels

1. Open `youtube_scraper.py`
2. Find the `CHANNELS = [` section (around line 50–80)
3. Add your channels inside the square brackets `[ ]`

**Format to follow:**
```python
CHANNELS = [
    {
        "url":      "https://www.youtube.com/@CHANNEL_HANDLE_HERE",
        "label":    "fake",
        "category": "satire",
    },
    {
        "url":      "https://www.youtube.com/@ANOTHER_CHANNEL",
        "label":    "real",
        "category": "news",
    },
]
```

**How to find a channel's URL:**
1. Go to any YouTube channel page
2. Look at the browser address bar — copy the full URL
3. It might look like:
   - `https://www.youtube.com/@SomoyTV`
   - `https://www.youtube.com/channel/UCxxxxxx`
   - Both formats work fine!

**Use `"label": "fake"` for fake/satire channels**
**Use `"label": "real"` for real news channels**

**Example with real verified Bangladeshi news channels:**
```python
CHANNELS = [
    # Add your fake channels here:
    {
        "url":      "https://www.youtube.com/@YourFakeChannel",
        "label":    "fake",
        "category": "satire",
    },

    # Verified real news channels:
    {
        "url":      "https://www.youtube.com/@somoynews360",
        "label":    "real",
        "category": "news",
    },
    {
        "url":      "https://www.youtube.com/@RtvNews",
        "label":    "real",
        "category": "news",
    },
    {
        "url":      "https://www.youtube.com/@EkattorTelevision",
        "label":    "real",
        "category": "news",
    },
    {
        "url":      "https://www.youtube.com/@JamunaTVbd",
        "label":    "real",
        "category": "news",
    },
    {
        "url":      "https://www.youtube.com/@channel24digital",
        "label":    "real",
        "category": "news",
    },
]
```

---

## ▶️ STEP 7 — Run the Scripts

Open PowerShell in the project folder (see Step 2) and run:

### To collect news articles from websites:
```
python scraper.py
```

### To collect YouTube video data:
```
python youtube_scraper.py
```

### You can run both — they save to the SAME file!
Both scripts add rows to `news_dataset.csv` automatically.

---

## 📊 What Does the Output Look Like?

All collected data goes into `news_dataset.csv`. Each row looks like:

| id | title | text | source | publish_date | category | label | url | content_hash |
|----|-------|------|--------|-------------|----------|-------|-----|--------------|
| 1 | বাংলাদেশে... | আজ সকালে... | Somoy TV | 2024-03-15 | news | real | https://... | a3f9c1b2 |
| 2 | ভাইরাল!! চাঞ্চ... | এই ভিডিওতে... | FakeChannel | 2024-02-10 | satire | fake | https://... | b7d2e4f1 |

- **title** = news headline or YouTube video title
- **text** = article body text or YouTube video description
- **source** = news website name or YouTube channel name
- **publish_date** = when it was published
- **label** = `real` or `fake` ← this is what your AI model will learn from
- **url** = link to the original article/video

---

## 👀 STEP 8 — How to Watch Progress While Running

**Option 1 — Watch the terminal**
The script prints each article as it's collected:
```
[1/300] (real) [Somoy TV] বাংলাদেশে বন্যা পরিস্থিতির উন্নতি...
[2/300] (fake) [EarkiHumor] ঢাকায় বৃষ্টির কারণে সকল মানুষ মাছ হয়ে গেছে...
```

**Option 2 — Open the CSV while it runs**
- Open `news_dataset.csv` in Excel or Google Sheets
- You'll see rows being added in real-time

**Option 3 — Check the log file**
- Open `scraper.log` or `youtube_scraper.log` in Notepad
- Shows detailed activity including any errors

---

## ⏹️ How to Stop and Resume

- Press **Ctrl + C** in the terminal to stop anytime
- Just run the same command again to **resume from where you stopped**
- It will NOT collect duplicates — it remembers everything via `visited_urls.txt`

---

## ⚙️ Optional Settings You Can Change

### In `scraper.py`:
Find these lines near the top and change the numbers:
```python
DEFAULT_MAX = 300      # How many articles to collect per run (increase for more)
MIN_WORD_COUNT = 50    # Skip articles shorter than this many words
```

### In `youtube_scraper.py`:
```python
DEFAULT_MAX = 5000     # Max videos to collect (set None for unlimited)
```

### Or use command options:
```
python scraper.py --max_articles 1000
python youtube_scraper.py --max 2000
python scraper.py --fresh           ← WARNING: deletes old data and starts over!
```

---

## 🔴 Common Problems & Fixes

| Problem | Fix |
|---------|-----|
| `python: command not found` | Python not installed correctly — reinstall and check "Add to PATH" |
| `pip: command not found` | Try `python -m pip install -r requirements.txt` instead |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| `API key not set` error | You forgot to add your API key in Step 5 |
| `quotaExceeded` error | YouTube daily limit hit — come back tomorrow (resets at midnight) |
| Script is very slow | Normal! It sleeps between requests so websites don't block it |
| Empty `news_dataset.csv` | Wait a few minutes — some sources take time to start |
| Script stopped by itself | Just run it again — it resumes where it stopped |

---

## 👥 Sharing With a Friend

**The simple way (no Git):**
1. Zip ONLY these 4 files:
   - `scraper.py`
   - `youtube_scraper.py`
   - `requirements.txt`
   - `README.md`
2. Send the zip via WhatsApp / Email / Google Drive
3. Your friend does Steps 1–7 on their computer
4. They also need their own YouTube API key (Step 4)

**Merging your datasets:**
When both of you have collected data, share your `news_dataset.csv` files.
The `content_hash` column prevents duplicates when merging.

To merge, run this in Python:
```python
import csv

files  = ["my_data.csv", "friends_data.csv"]
output = "merged_final.csv"
fields = ["id","title","text","source","publish_date","category","label","url","content_hash"]

seen, rows = set(), []
for fname in files:
    with open(fname, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            h = row.get("content_hash","")
            if h and h not in seen:
                seen.add(h)
                rows.append(row)

for i, row in enumerate(rows, 1):
    row["id"] = i

with open(output, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

print(f"Done! {len(rows)} unique rows saved to {output}")
```
Save this as `merge.py` and run: `python merge.py`

---

## 🎯 How Much Data Do You Need?

For a good Deep Learning model:

| Label | Minimum | Good | Excellent |
|-------|---------|------|-----------|
| `real` | 500 | 2,000 | 5,000+ |
| `fake` | 500 | 2,000 | 5,000+ |

**Plan:** Run both scripts every day for a few days. Each run collects 200–500 new items.

---

## 📞 Quick Summary — The 3 Commands You'll Use Most

```bash
# 1. Collect news articles (no API key needed)
python scraper.py

# 2. Collect YouTube videos (needs API key + channels configured)
python youtube_scraper.py

# 3. Merge two CSV files from you and your friend
python merge.py
```

That's it! 🎉
