#!/usr/bin/env python3
# =============================================================================
#  YouTube Channel Scraper  v2.0
#  Output format matches news_dataset.csv exactly — easy to merge datasets.
#
#  CSV Fields:
#    id, title, text (description), source (channel), publish_date,
#    category, label, url (video url), content_hash
#
#  HOW TO GET A FREE API KEY (3 minutes):
#    1. https://console.cloud.google.com/  → create project
#    2. Search "YouTube Data API v3" → Enable
#    3. Credentials → Create API Key → copy it
#    4. Paste below or: set YOUTUBE_API_KEY=your_key  (Windows)
#
#  USAGE:
#    python youtube_scraper.py                    # scrape all channels listed below
#    python youtube_scraper.py --fresh            # delete old data first, then scrape
#    python youtube_scraper.py --max 1000         # stop after 1000 videos
# =============================================================================

import os
import csv
import sys
import json
import time
import hashlib
import logging
import argparse
from datetime import datetime
from urllib.parse import urlencode, urlparse

import requests

# ─────────────────────────────────────────────────────────────────────────────
#  ★  SET YOUR API KEY HERE  (or use env var YOUTUBE_API_KEY)
# ─────────────────────────────────────────────────────────────────────────────
API_KEY = os.environ.get("YOUTUBE_API_KEY", "AIzaSyAxJ144u8JNMdGY3IoZm4boTJNnRsNJqp8")
# ─────────────────────────────────────────────────────────────────────────────

# =============================================================================
#  ★  ADD YOUR CHANNELS HERE
#  Paste any YouTube channel URL format — the script handles all of them:
#    https://www.youtube.com/@ChannelHandle
#    https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxx
#    https://www.youtube.com/c/ChannelName
#    https://www.youtube.com/user/UserName
#
#  "label"    → "fake" or "real"
#  "category" → whatever makes sense for your dataset
# =============================================================================

DEFAULT_CHANNEL_MAX = 50  # videos per channel unless overridden below

CHANNELS = [
    # ── Fake / Satire channels ────────────────────────────────────────────────
    # Add your fake news channels here, example:
     {
        "url": "https://www.youtube.com/@KESTV",
        "label": "fake",
        "category": "politics",
        "max_videos": 170,  # collect up to 100 from this channel
    },
    {
        "url": "https://www.youtube.com/@%E0%A6%A6%E0%A7%87%E0%A6%B6%E0%A7%87%E0%A6%B0%E0%A6%B0%E0%A6%BE%E0%A6%9C%E0%A6%A8%E0%A7%80%E0%A6%A4%E0%A6%BF%E0%A6%B0",
        "label": "fake",
        "category": "politics",
        "max_videos": 80,  # collect up to 100 from this channel
    },
    {
        "url": "https://www.youtube.com/@takepartinsolaimananalysis7024",
        "label": "fake",
        "category": "news",
        "max_videos": 20,
        # no max_videos → uses DEFAULT_CHANNEL_MAX (50)
    },
    {
        "url": "https://www.youtube.com/@solaimananalysis7238",
        "label": "fake",
        "category": "satire",
        "max_videos": 30,
    },
    {
        "url": "https://www.youtube.com/@NotunShomoy",
        "label": "fake",
        "category": "news",
    },
    {
        "url": "https://www.youtube.com/@BioscopeEntertainment",
        "label": "fake",
        "category": "news",
    },
    {
        "url": "https://www.youtube.com/@aalorsondhane",
        "label": "fake",
        "category": "politics",
    },
    {
        "url": "https://www.youtube.com/@PadatikOfficial",
        "label": "fake",
        "category": "news",
    },
    {
        "url": "https://www.youtube.com/@JNewsTV-r9i",
        "label": "fake",
        "category": "news",
    },
        {
        "url": "https://www.youtube.com/@PoliticalTolkshowBD",
        "label": "fake",
        "category": "politics",
    },
    {
        "url": "https://www.youtube.com/@hamidurnews",
        "label": "fake",
        "category": "news",
    },
    {
        "url": "https://www.youtube.com/@ZamunaTvAlochona",
        "label": "fake",
        "category": "politics",
    },
    {
        "url": "https://www.youtube.com/@channel_unique",
        "label": "fake",
        "category": "satire",
         "max_videos": 70,
    },
    {
        "url": "https://www.youtube.com/@worldbanglanewz",
        "label": "fake",
        "category": "politics",
         "max_videos": 80,
    },
    {
        "url": "https://www.youtube.com/@PodcastNewsBengali",
        "label": "fake",
        "category": "national",
    },
    {
        "url": "https://www.youtube.com/@uniquefact7901",
        "label": "fake",
        "category": "news",
        "max_videos": 70,
    },
    {
        "url": "https://www.youtube.com/@jonotarrajnitibd",
        "label": "fake",
        "category": "politics",
    },
    {
        "url": "https://www.youtube.com/@banglakathan",
        "label": "fake",
        "category": "politics",
        "max_videos": 20,
    },
    {
        "url": "https://www.youtube.com/@StarExpressbd",
        "label": "fake",
        "category": "satire",
        "max_videos": 20,
    },
    {
        "url": "https://www.youtube.com/@MRBANGLANEWS24",
        "label": "fake",
        "category": "satire",
        "max_videos": 30,
    },
    {
        "url": "https://www.youtube.com/@Changetvpress",
        "label": "fake",
        "category": "news",
        "max_videos": 20,
    },
    {
        "url": "https://www.youtube.com/@filmynews-sk4bb",
        "label": "fake",
        "category": "satire",
        "max_videos": 120,
    },
    {
        "url": "https://www.youtube.com/@NewsTVBangla-24",
        "label": "fake",
        "category": "political",
    },
    {
        "url": "https://www.youtube.com/@TRENDS_NEWS_69",
        "label": "fake",
        "category": "news",
        "max_videos": 100,
    },
    {
        "url": "https://www.youtube.com/@NewsTrendsBangla",
        "label": "fake",
        "category": "news",
        "max_videos": 100,
    },
    {
        "url": "https://www.youtube.com/@FaporbazMe",
        "label": "fake",
        "category": "satire",
    },
    {
        "url": "https://www.youtube.com/@trendnews855",
        "label": "fake",
        "category": "satire",
        "max_videos": 20,
    },
    {
        "url": "https://www.youtube.com/@ChannelSOnline",
        "label": "fake",
        "category": "satire",
        "max_videos": 30,
    },
   
    # ── Real news channels ────────────────────────────────────────────────────
    # {
    #     "url":      "https://www.youtube.com/@SomoyTV",
    #     "label":    "real",
    #     "category": "news",
    # },
    # {
    #     "url":      "https://www.youtube.com/channel/UCGKjCHHGcwOMFDr2I-8JZFQ",
    #     "label":    "real",
    #     "category": "news",
    # },
]
# =============================================================================

CSV_FILE = "news_dataset.csv"  # same file as scraper.py — they merge!
VISITED_FILE = "youtube_visited.txt"  # separate visited log for YouTube
LOG_FILE = "youtube_scraper.log"
YT_BASE = "https://www.googleapis.com/youtube/v3"

DEFAULT_MAX = 5000  # safety cap per run (set None for no limit)
BATCH_SAVE = 20  # flush to CSV every N records
REQUEST_DELAY = 0.3  # seconds between API calls

CSV_FIELDS = [
    "id",
    "title",
    "text",
    "source",
    "publish_date",
    "category",
    "label",
    "url",
    "content_hash",
]


# =============================================================================
#  LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# =============================================================================
#  HELPERS
# =============================================================================


def content_hash(title: str, text: str) -> str:
    """Same hash function as scraper.py — prevents cross-source duplicates."""
    raw = (title.strip() + " " + text.strip()[:500]).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def load_visited() -> set:
    visited = set()
    if os.path.exists(VISITED_FILE):
        with open(VISITED_FILE, "r", encoding="utf-8") as f:
            for line in f:
                v = line.strip()
                if v:
                    visited.add(v)
    return visited


def save_visited(visited: set):
    with open(VISITED_FILE, "w", encoding="utf-8") as f:
        for v in sorted(visited):
            f.write(v + "\n")


def get_next_id() -> int:
    """Read the existing CSV and return the next sequential ID."""
    if not os.path.exists(CSV_FILE):
        return 1
    try:
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        return max(len(rows), 1)  # len includes header row
    except Exception:
        return 1


def append_to_csv(records: list[dict]):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        for rec in records:
            writer.writerow({k: rec.get(k, "") for k in CSV_FIELDS})


# =============================================================================
#  YOUTUBE API CALLS
# =============================================================================


def _api_get(endpoint: str, params: dict) -> dict | None:
    """Raw API GET — returns parsed JSON or None on error."""
    params["key"] = API_KEY
    url = f"{YT_BASE}/{endpoint}?{urlencode(params)}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 403:
            data = resp.json()
            reason = data.get("error", {}).get("errors", [{}])[0].get("reason", "")
            if reason == "quotaExceeded":
                log.error(
                    "❌  Daily quota exceeded! Come back tomorrow or use a different API key."
                )
                raise SystemExit(1)
        resp.raise_for_status()
        return resp.json()
    except SystemExit:
        raise
    except requests.RequestException as exc:
        log.warning(f"  API error [{endpoint}]: {exc}")
        return None


def resolve_channel_id(url: str) -> tuple[str, str]:
    """
    Given any YouTube channel URL, return (channel_id, channel_title).
    Handles:
      @Handle  →  channels?forHandle
      /channel/UCxxx  →  direct extraction
      /c/name or /user/name  →  channels?forUsername
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    # Format: /channel/UCxxxxxxxxxx  — extract directly
    if path.startswith("channel/UC"):
        ch_id = path.split("/")[1]
        data = _api_get("channels", {"part": "snippet", "id": ch_id})
        if data and data.get("items"):
            return ch_id, data["items"][0]["snippet"]["title"]
        return ch_id, ch_id

    # Format: /@Handle
    if path.startswith("@"):
        handle = path  # e.g. "@SomoyTV"
        data = _api_get("channels", {"part": "id,snippet", "forHandle": handle})
        if data and data.get("items"):
            item = data["items"][0]
            return item["id"], item["snippet"]["title"]
        log.warning(f"  Could not resolve handle: {handle}")
        return "", handle

    # Format: /c/customname or /user/username
    parts = path.split("/")
    username = parts[-1] if parts else ""
    data = _api_get("channels", {"part": "id,snippet", "forUsername": username})
    if data and data.get("items"):
        item = data["items"][0]
        return item["id"], item["snippet"]["title"]

    log.warning(f"  Could not resolve channel URL: {url}")
    return "", url


def get_uploads_playlist_id(channel_id: str) -> str | None:
    """
    Every YouTube channel has a hidden 'uploads' playlist.
    This is the most quota-efficient way to list all videos (1 unit per page, not 100).
    """
    data = _api_get(
        "channels",
        {
            "part": "contentDetails",
            "id": channel_id,
        },
    )
    if not data or not data.get("items"):
        return None
    return (
        data["items"][0]
        .get("contentDetails", {})
        .get("relatedPlaylists", {})
        .get("uploads")
    )


def get_playlist_video_ids(
    playlist_id: str, page_token: str = None
) -> tuple[list[dict], str | None]:
    """
    Fetch one page of video IDs + basic info from an uploads playlist.
    Returns (list of {video_id, title, description, published_at}), next_page_token.
    Uses 1 quota unit per call (much cheaper than search.list = 100 units).
    """
    params = {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": 50,
    }
    if page_token:
        params["pageToken"] = page_token

    data = _api_get("playlistItems", params)
    if not data:
        return [], None

    items = []
    for item in data.get("items", []):
        snip = item.get("snippet", {})
        vid_id = snip.get("resourceId", {}).get("videoId", "")
        if not vid_id or vid_id == "deleted":
            continue
        pub = snip.get("publishedAt", "")
        items.append(
            {
                "video_id": vid_id,
                "title": snip.get("title", "").strip(),
                "description": snip.get("description", "").strip(),
                "published_at": pub[:10] if pub else "",  # YYYY-MM-DD
            }
        )

    next_token = data.get("nextPageToken")
    return items, next_token


# =============================================================================
#  MAIN SCRAPE LOGIC
# =============================================================================


def scrape_channel(
    ch_info: dict,
    visited: set,
    id_counter: list,
    global_max: int | None,
    global_collected: list,
) -> list[dict]:
    """
    Scrape videos from one channel, respecting both:
      • per-channel max  → ch_info.get("max_videos") or DEFAULT_CHANNEL_MAX
      • global max       → global_max (from --max flag), counts across all channels
    Returns list of CSV-ready record dicts.
    """
    url = ch_info["url"]
    label = ch_info["label"]
    category = ch_info.get("category", "youtube")

    # Per-channel cap: use explicit value, or fall back to DEFAULT_CHANNEL_MAX
    ch_max = ch_info.get("max_videos", DEFAULT_CHANNEL_MAX)

    log.info(f"\n  📺 Resolving channel: {url}")
    ch_id, ch_title = resolve_channel_id(url)
    if not ch_id:
        log.warning(f"  Skipping — could not resolve channel: {url}")
        return []

    log.info(
        f"  ✅ Channel: '{ch_title}'  ID: {ch_id}  " f"label={label}  max={ch_max}"
    )

    playlist_id = get_uploads_playlist_id(ch_id)
    if not playlist_id:
        log.warning(f"  Could not find uploads playlist for {ch_title}")
        return []

    collected = []
    page_token = None
    page_num = 0

    while True:
        # Stop if per-channel cap reached
        if len(collected) >= ch_max:
            log.info(f"    [{ch_title}] Per-channel limit ({ch_max}) reached.")
            break
        # Stop if global cap reached
        if global_max and (len(global_collected) + len(collected)) >= global_max:
            log.info(f"    [{ch_title}] Global limit ({global_max}) reached.")
            break

        page_num += 1
        items, page_token = get_playlist_video_ids(playlist_id, page_token)
        time.sleep(REQUEST_DELAY)

        if not items:
            log.info(f"    No more items on page {page_num}")
            break

        for item in items:
            # Re-check both caps inside inner loop
            if len(collected) >= ch_max:
                break
            if global_max and (len(global_collected) + len(collected)) >= global_max:
                break

            vid_id = item["video_id"]
            if vid_id in visited:
                continue

            title = item["title"]
            text = item["description"]
            pub = item["published_at"]
            vid_url = f"https://www.youtube.com/watch?v={vid_id}"
            chash = content_hash(title, text)

            if not title:
                continue

            visited.add(vid_id)

            record = {
                "id": id_counter[0],
                "title": title,
                "text": text,
                "source": ch_title,
                "publish_date": pub,
                "category": category,
                "label": label,
                "url": vid_url,
                "content_hash": chash,
            }
            id_counter[0] += 1
            collected.append(record)

            if len(collected) % 50 == 0:
                log.info(f"    [{ch_title}] {len(collected)} videos so far...")

        if not page_token:
            log.info(f"    [{ch_title}] All pages done (page {page_num})")
            break

    log.info(f"  ✅ [{ch_title}] Total new videos: {len(collected)}")
    return collected


def run(max_videos: int | None = None, fresh: bool = False):

    # ── Pre-flight check ──────────────────────────────────────────────────────
    if API_KEY == "YOUR_API_KEY_HERE":
        print("\n" + "=" * 65)
        print("  ❌  ERROR: YouTube API key not set!")
        print("  Edit youtube_scraper.py and set API_KEY = 'AIza...'")
        print("  OR run:  $env:YOUTUBE_API_KEY = 'AIza...'  (PowerShell)")
        print("  Get free key: https://console.cloud.google.com/")
        print("=" * 65 + "\n")
        raise SystemExit(1)

    if not CHANNELS:
        print("\n" + "=" * 65)
        print("  ❌  No channels configured!")
        print("  Edit youtube_scraper.py and add channels to CHANNELS list.")
        print("=" * 65 + "\n")
        raise SystemExit(1)

    if fresh:
        for f in [VISITED_FILE]:  # we keep CSV — fresh only resets visited
            if os.path.exists(f):
                os.remove(f)
                log.info(f"  🗑  Deleted {f}")

    visited = load_visited()
    id_counter = [get_next_id()]  # mutable counter shared across channels

    log.info("=" * 68)
    log.info(f"▶ YOUTUBE SCRAPE START  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log.info(f"   Channels : {len(CHANNELS)}   max_videos={max_videos or 'unlimited'}")
    log.info("=" * 68)

    total_new = 0
    buffer = []

    all_collected: list[dict] = []  # track total across channels for global cap

    for ch_info in CHANNELS:
        records = scrape_channel(
            ch_info, visited, id_counter, max_videos, all_collected
        )
        all_collected.extend(records)

        for rec in records:
            buffer.append(rec)
            total_new += 1

            if len(buffer) >= BATCH_SAVE:
                append_to_csv(buffer)
                save_visited(visited)
                buffer.clear()
                log.info(f"  💾 Saved batch — total so far: {total_new}")

    # Final flush
    if buffer:
        append_to_csv(buffer)
        save_visited(visited)

    # ── Summary ───────────────────────────────────────────────────────────────
    from collections import Counter

    label_counts: Counter = Counter()
    if os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    label_counts[row.get("label", "?")] += 1
        except Exception:
            pass

    log.info("=" * 68)
    log.info("✅  YOUTUBE SCRAPE COMPLETE")
    log.info(f"   New videos this run : {total_new}")
    log.info(f"   CSV label breakdown :")
    for lbl in ["real", "fake"]:
        log.info(f"      {lbl:6s}: {label_counts.get(lbl, 0)}")
    log.info(f"   Saved to: {CSV_FILE}")
    log.info("=" * 68)

    print(f"\n{'='*68}")
    print("  ✅  DONE")
    print(f"  New videos : {total_new}")
    print(f"  real={label_counts.get('real',0)}   fake={label_counts.get('fake',0)}")
    print(f"  CSV: {CSV_FILE}  (merged with news articles)")
    print(f"{'='*68}\n")


# =============================================================================
#  CLI
# =============================================================================


def main():
    ap = argparse.ArgumentParser(
        description="YouTube Channel Scraper — output matches news_dataset.csv format"
    )
    ap.add_argument(
        "--max",
        type=int,
        default=None,
        help="Max total videos to collect (default: no limit)",
    )
    ap.add_argument(
        "--fresh",
        action="store_true",
        help="Reset visited log and re-scrape from scratch",
    )
    ap.add_argument(
        "--apikey",
        type=str,
        default=None,
        help="YouTube API key (overrides env var / hardcoded key)",
    )
    args = ap.parse_args()

    global API_KEY
    if args.apikey:
        API_KEY = args.apikey

    run(max_videos=args.max, fresh=args.fresh)


if __name__ == "__main__":
    main()
