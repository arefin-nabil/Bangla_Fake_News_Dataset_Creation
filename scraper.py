#!/usr/bin/env python3
# =============================================================================
#  Bangla News Dataset Scraper  v4.0
#  Classes : real | fake   (only 2 labels — by design)
#  Sources :
#    REAL  → Prothom Alo, Samakal, Naya Diganta, BD Pratidin,
#             Jugantor, Ittefaq, Amar Desh, Shomoyeralo,
#             Daily Inqilab, Bonik Barta
#    FAKE  → earki.co (humor, satire, news, interview sections)
#             — satirical / parody / fake-news content
#  Fact-check sources are DISABLED for now (label="disabled").
#  Facebook page scraping → NOT possible via web-scraping (see note below).
# =============================================================================
#
#  ── FACEBOOK SCRAPING NOTE ──────────────────────────────────────────────────
#  Facebook blocks all public scraping via bot-detection, login walls, and
#  dynamic JavaScript rendering.  Options if you need FB data:
#    1. Facebook Graph API  (requires an approved App + page tokens)
#    2. CrowdTangle         (academic / media research tool by Meta)
#    3. Manual export       (download your own page data from Settings)
#  Plain requests/BeautifulSoup CANNOT reliably scrape FB pages.
#  → Provide FB page links and we can discuss the API approach.
# ────────────────────────────────────────────────────────────────────────────

import os
import re
import csv
import sys
import json
import time
import random
import hashlib
import logging
import argparse
from datetime import datetime, date, timedelta
from urllib.parse import urljoin, urlparse

# ── CSV field size limit (handles very long article bodies) ───────────────────
_max_int = sys.maxsize
while True:
    try:
        csv.field_size_limit(_max_int)
        break
    except OverflowError:
        _max_int = int(_max_int / 10)

# ── Force UTF-8 output ────────────────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


# =============================================================================
#  CONFIGURATION
# =============================================================================

CSV_FILE         = "news_dataset.csv"
VISITED_FILE     = "visited_urls.txt"
STATE_FILE       = "last_run_state.json"
LOG_FILE         = "scraper.log"

DEFAULT_START    = date(2025, 1, 1)
DEFAULT_END      = date.today()

# Daily / per-run article limit
DEFAULT_MAX      = 300
BATCH_SAVE_EVERY = 10           # flush to CSV every N articles
MIN_WORD_COUNT   = 50           # earki articles can be shorter (humor/satire)

# Sitemap sampling
SITEMAP_DAYS_SAMPLE = 45        # how many recent daily sitemaps to walk per source

# Crawl delays (seconds)
DELAY_MIN        = 1.5
DELAY_MAX        = 3.5
SITEMAP_DELAY    = 0.4
REQUEST_TIMEOUT  = 20

# How many listing pages to paginate for earki
EARKI_MAX_PAGES  = 80           # ~15 articles/page × 80 = ~1200 per section


# =============================================================================
#  SOURCE REGISTRY
# =============================================================================

SOURCES = [
    # ── REAL NEWS (sitemap-based) ─────────────────────────────────────────────
    {
        "name":         "Prothom Alo",
        "label":        "real",
        "parser":       "prothomalo",
        "category":     "national",
        "sitemap_base": "https://www.prothomalo.com/sitemap/sitemap-daily-{date}.xml",
        "urls":         [],
    },
    {
        "name":         "Samakal",
        "label":        "real",
        "parser":       "samakal",
        "category":     "national",
        "sitemap_base": "https://samakal.com/sitemap/sitemap-daily-{date}.xml",
        "urls":         [],
    },
    {
        "name":         "Naya Diganta",
        "label":        "real",
        "parser":       "generic_news",
        "category":     "national",
        "sitemap_base": "https://dailynayadiganta.com/sitemap/{date}.xml",
        "urls":         [],
    },
    {
        "name":         "BD Pratidin",
        "label":        "real",
        "parser":       "bd_pratidin",
        "category":     "national",
        "sitemap_base": "https://www.bd-pratidin.com/daily-sitemap/{date}/sitemap.xml",
        "urls":         [],
    },

    # ── REAL NEWS (category-page-based) ──────────────────────────────────────
    {
        "name":         "Jugantor",
        "label":        "real",
        "parser":       "jugantor",
        "category":     "national",
        "sitemap_base": None,
        "urls": [
            "https://www.jugantor.com/national",
            "https://www.jugantor.com/politics",
            "https://www.jugantor.com/economics",
            "https://www.jugantor.com/international",
        ],
    },
    {
        "name":         "Ittefaq",
        "label":        "real",
        "parser":       "ittefaq",
        "category":     "national",
        "sitemap_base": None,
        "urls": [
            "https://www.ittefaq.com.bd/national",
            "https://www.ittefaq.com.bd/politics",
            "https://www.ittefaq.com.bd/world-news",
            "https://www.ittefaq.com.bd/business",
        ],
    },
    {
        "name":         "Amar Desh",
        "label":        "real",
        "parser":       "generic_news",
        "category":     "national",
        "sitemap_base": None,
        "urls": [
            "https://www.dailyamardesh.com/national",
            "https://www.dailyamardesh.com/politics",
            "https://www.dailyamardesh.com/business",
        ],
    },
    {
        "name":         "Shomoyeralo",
        "label":        "real",
        "parser":       "shomoyeralo",
        "category":     "national",
        "sitemap_base": None,
        "urls": [
            "https://www.shomoyeralo.com/menu/102",   # national
            "https://www.shomoyeralo.com/menu/115",   # politics
            "https://www.shomoyeralo.com/menu/116",   # international
            "https://www.shomoyeralo.com/menu/130",   # economy
        ],
    },
    {
        "name":         "Daily Inqilab",
        "label":        "real",
        "parser":       "generic_news",
        "category":     "national",
        "sitemap_base": None,
        "urls": [
            "https://dailyinqilab.com/national",
            "https://dailyinqilab.com/politics",
            "https://dailyinqilab.com/economy",
        ],
    },
    {
        "name":         "Bonik Barta",
        "label":        "real",
        "parser":       "generic_news",
        "category":     "business",
        "sitemap_base": None,
        "urls": [
            "https://bonikbarta.com/economy",
            "https://bonikbarta.com/stock",
            "https://bonikbarta.com/industry",
        ],
    },

    # ── FAKE NEWS SOURCE: earki.co (Bangla satire / parody / humor site) ─────
    # All content here is intentionally fictional / satirical — label = fake
    {
        "name":         "Earki Humor",
        "label":        "fake",
        "parser":       "earki",
        "category":     "humor",
        "sitemap_base": None,
        "urls": [
            "https://www.earki.co/humor",
        ],
    },
    {
        "name":         "Earki Satire",
        "label":        "fake",
        "parser":       "earki",
        "category":     "satire",
        "sitemap_base": None,
        "urls": [
            "https://www.earki.co/satire",
        ],
    },
    {
        "name":         "Earki News",
        "label":        "fake",
        "parser":       "earki",
        "category":     "fake-news",
        "sitemap_base": None,
        "urls": [
            "https://www.earki.co/news",
        ],
    },
    {
        "name":         "Earki Interview",
        "label":        "fake",
        "parser":       "earki",
        "category":     "fake-interview",
        "sitemap_base": None,
        "urls": [
            "https://www.earki.co/interview",
        ],
    },

    # ── FACT-CHECK SOURCES  (DISABLED for now — set label="disabled") ─────────
    # Uncomment label line and change to "auto" to re-enable in future.
    {
        "name":         "Rumor Scanner",
        "label":        "disabled",   # change to "auto" to enable
        "parser":       "rumorscanner",
        "category":     "fact-check",
        "sitemap_base": None,
        "urls": [
            "https://rumorscanner.com/category/fact-check/national",
            "https://rumorscanner.com/category/fact-check/international",
            "https://rumorscanner.com/category/fact-check/politics",
            "https://rumorscanner.com/category/fact-check/health",
        ],
    },
    {
        "name":         "Fact Watch",
        "label":        "disabled",
        "parser":       "factwatch",
        "category":     "fact-check",
        "sitemap_base": None,
        "urls": [
            "https://www.fact-watch.org/category/%e0%a6%ab%e0%a7%8d%e0%a6%af%e0%a6%be%e0%a6%95%e0%a7%8d%e0%a6%9f%e0%a6%9a%e0%a7%87%e0%a6%95/",
        ],
    },
    {
        "name":         "Jachai",
        "label":        "disabled",
        "parser":       "jachai",
        "category":     "fact-check",
        "sitemap_base": None,
        "urls": [
            "https://jachai.org/fact-checks",
        ],
    },
    {
        "name":         "Rumor Inspector",
        "label":        "disabled",
        "parser":       "rumorinspector",
        "category":     "fact-check",
        "sitemap_base": None,
        "urls": [
            "https://rumorinspector.com/category/fact-check/",
        ],
    },
    {
        "name":         "Boom BD",
        "label":        "disabled",
        "parser":       "boombd",
        "category":     "fact-check",
        "sitemap_base": None,
        "urls": [
            "https://www.boombd.com/fake-news",
            "https://www.boombd.com/fact-file",
        ],
    },
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


# =============================================================================
#  HTTP SESSION
# =============================================================================

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "bn-BD,bn;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})


def fetch(url: str, retries: int = 3) -> BeautifulSoup | None:
    for attempt in range(1, retries + 1):
        try:
            resp = SESSION.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as exc:
            wait = attempt * 4
            log.warning(f"  Fetch {attempt}/{retries} failed [{url}]: {exc}")
            if attempt < retries:
                time.sleep(wait)
    return None


def fetch_xml(url: str, retries: int = 3) -> BeautifulSoup | None:
    for attempt in range(1, retries + 1):
        try:
            resp = SESSION.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return BeautifulSoup(resp.text, features="xml")
        except requests.RequestException as exc:
            wait = attempt * 4
            log.warning(f"  XML fetch {attempt}/{retries} failed [{url}]: {exc}")
            if attempt < retries:
                time.sleep(wait)
    return None


def polite_sleep():
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))


# =============================================================================
#  STATE & STORAGE
# =============================================================================

CSV_FIELDS = ["id", "title", "text", "source", "publish_date",
              "category", "label", "url", "content_hash"]


def content_hash(title: str, text: str) -> str:
    """Short SHA-256 fingerprint for deduplication across re-posts."""
    raw = (title.strip() + " " + text.strip()[:500]).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def load_visited() -> set:
    visited = set()
    if os.path.exists(VISITED_FILE):
        with open(VISITED_FILE, "r", encoding="utf-8") as f:
            for line in f:
                visited.add(line.strip())
    return visited


def save_visited(visited: set):
    with open(VISITED_FILE, "w", encoding="utf-8") as f:
        for u in sorted(visited):
            f.write(u + "\n")


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"total_collected": 0, "last_run": None}


def save_state(state: dict):
    state["last_run"] = datetime.now().isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def load_seen_hashes() -> set:
    """Load all content hashes already stored in the CSV to catch cross-site dupes."""
    hashes = set()
    if not os.path.exists(CSV_FILE):
        return hashes
    try:
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                h = row.get("content_hash", "").strip()
                if h:
                    hashes.add(h)
    except Exception:
        pass
    return hashes


def get_next_id() -> int:
    if not os.path.exists(CSV_FILE):
        return 1
    try:
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        return max(len(rows), 1)
    except Exception:
        return 1


def append_to_csv(articles: list[dict]):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        for art in articles:
            writer.writerow({k: art.get(k, "") for k in CSV_FIELDS})


# =============================================================================
#  DATE HELPERS
# =============================================================================

def date_range(start: date, end: date):
    current = end
    while current >= start:
        yield current
        current -= timedelta(days=1)


def parse_date_str(text: str) -> date | None:
    if not text:
        return None
    text = text.strip()
    for pat in [
        r"(\d{4})-(\d{2})-(\d{2})",
        r"(\d{2})/(\d{2})/(\d{4})",
    ]:
        m = re.search(pat, text)
        if m:
            try:
                g = m.groups()
                if len(g) == 3:
                    y, mo, d = int(g[0]), int(g[1]), int(g[2])
                    return date(y, mo, d)
            except ValueError:
                continue
    return None


def in_date_range(d: date | None, start: date, end: date) -> bool:
    if d is None:
        return True
    return start <= d <= end


# =============================================================================
#  SITEMAP HELPERS  (generator-based — no upfront bulk loading)
# =============================================================================

def _sitemap_urls(sitemap_url: str) -> list[str]:
    soup = fetch_xml(sitemap_url)
    if not soup:
        return []
    return [loc.get_text(strip=True) for loc in soup.find_all("loc")]


def build_sitemap_urls(source: dict, start: date, end: date):
    """Yield article URLs one sitemap-day at a time."""
    template = source["sitemap_base"]
    all_dates = list(date_range(start, end))
    sampled   = all_dates[:SITEMAP_DAYS_SAMPLE]

    log.info(f"  [{source['name']}] Walking {len(sampled)} daily sitemaps...")
    for i, d in enumerate(sampled, 1):
        sitemap_url = template.format(date=d.strftime("%Y-%m-%d"))
        for url in _sitemap_urls(sitemap_url):
            yield url
        if i % 15 == 0:
            log.info(f"    [{source['name']}] {i}/{len(sampled)} sitemaps done")
        time.sleep(SITEMAP_DELAY)


# =============================================================================
#  LISTING-PAGE CRAWLER  (generic — for real-news category pages)
# =============================================================================

def crawl_listing(base_url: str, max_pages: int = 12):
    """Yield article URLs discovered by paginating a category/listing page."""
    domain = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
    seen   = set()

    for page_num in range(1, max_pages + 1):
        page_url = base_url if page_num == 1 else f"{base_url.rstrip('/')}/page/{page_num}/"

        soup = fetch(page_url)
        if not soup:
            break

        found_any = False
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.startswith("http"):
                href = urljoin(domain, href)
            if urlparse(href).netloc != urlparse(domain).netloc:
                continue
            path = urlparse(href).path
            if re.search(r"/(page|category|tag|search|author|about|contact|archive|menu)", path):
                continue
            if path.count("/") >= 2 and len(path) > 10 and href not in seen:
                seen.add(href)
                found_any = True
                yield href

        if not found_any:
            break

        polite_sleep()


# =============================================================================
#  EARKI.CO LISTING CRAWLER
#  URL pattern for listing pages: https://www.earki.co/humor?page=2
#  URL pattern for articles:      https://www.earki.co/humor/article/11798/slug
# =============================================================================

def crawl_earki_listing(base_url: str, max_pages: int = EARKI_MAX_PAGES):
    """
    Yield earki.co article URLs from a section listing page.
    Pagination uses ?page=N (not /page/N/).
    Stops early if a page returns the same articles as page 1 (loop guard).
    """
    seen      = set()
    first_set = None          # articles found on page 1 (loop-detection)
    domain    = "https://www.earki.co"

    # Pattern that matches earki article links, e.g. /humor/article/11798/...
    article_re = re.compile(r"^/[a-z]+/article/\d+/", re.I)

    for page_num in range(1, max_pages + 1):
        if page_num == 1:
            page_url = base_url
        else:
            page_url = f"{base_url}?page={page_num}"

        soup = fetch(page_url)
        if not soup:
            log.info(f"    [earki] page {page_num} fetch failed — stopping")
            break

        page_articles = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            # Normalise relative paths
            if href.startswith("/"):
                href = domain + href
            if not href.startswith(domain):
                continue
            path = urlparse(href).path
            if article_re.match(path) and href not in seen:
                seen.add(href)
                page_articles.append(href)

        if not page_articles:
            log.info(f"    [earki] no articles on page {page_num} — done")
            break

        # Loop detection: if page 2+ returns the exact same set as page 1
        if first_set is None:
            first_set = set(page_articles)
        elif page_num > 1 and set(page_articles) == first_set:
            log.info(f"    [earki] page {page_num} same as page 1 — pagination ended")
            break

        log.info(f"    [earki] page {page_num}: {len(page_articles)} new article links")
        yield from page_articles
        polite_sleep()


# =============================================================================
#  URL DISPATCHER
# =============================================================================

def get_urls_for_source(source: dict, start: date, end: date):
    """Generator: yield candidate URLs from this source's sitemap or listing pages."""
    if source.get("sitemap_base"):
        yield from build_sitemap_urls(source, start, end)
    elif source["parser"] == "earki":
        for seed in source["urls"]:
            log.info(f"  Crawling earki listing: {seed}")
            yield from crawl_earki_listing(seed)
            polite_sleep()
    else:
        for seed in source["urls"]:
            log.info(f"  Crawling listing: {seed}")
            yield from crawl_listing(seed)
            polite_sleep()


# =============================================================================
#  UNIVERSAL PARSE HELPERS
# =============================================================================

def _extract_pub_date(soup: BeautifulSoup) -> date | None:
    # 1) JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            for item in (data if isinstance(data, list) else [data]):
                ds = item.get("datePublished") or item.get("dateModified")
                if ds:
                    d = parse_date_str(ds)
                    if d:
                        return d
        except Exception:
            pass
    # 2) OG / article meta
    for prop in ["article:published_time", "article:modified_time", "og:updated_time", "pubdate"]:
        m = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        if m:
            d = parse_date_str(m.get("content", ""))
            if d:
                return d
    # 3) itemprop
    m = soup.find(attrs={"itemprop": "datePublished"})
    if m:
        d = parse_date_str(m.get("content", "") or m.get_text())
        if d:
            return d
    # 4) <time>
    t = soup.find("time")
    if t:
        d = parse_date_str(t.get("datetime", "") or t.get_text())
        if d:
            return d
    return None


def _generic_body(soup: BeautifulSoup) -> str:
    body = None
    for cls_pat in [r"article.?body|news.?body|post.?body|entry.?content",
                    r"detail|story|content|article"]:
        body = soup.find("div", class_=re.compile(cls_pat, re.I))
        if body:
            break
    if not body:
        body = soup.find("div", {"data-story-element": True})
    if not body:
        body = soup.find("article")
    return " ".join(p.get_text(" ", strip=True) for p in (body.find_all("p") if body else []))


# =============================================================================
#  SITE-SPECIFIC PARSERS
# =============================================================================

def parse_prothomalo(soup: BeautifulSoup, url: str) -> dict | None:
    title_tag = soup.find("h1") or soup.find("meta", property="og:title")
    title = (title_tag.get("content") if title_tag and title_tag.name == "meta"
             else title_tag.get_text(strip=True) if title_tag else "")
    body = soup.find("div", {"data-story-element": True}) or \
           soup.find("div", class_=re.compile(r"story|article|content", re.I)) or \
           soup.find("article")
    text = " ".join(p.get_text(" ", strip=True) for p in (body.find_all("p") if body else []))
    pub_date = _extract_pub_date(soup)
    parts = urlparse(url).path.strip("/").split("/")
    category = parts[0] if parts else "national"
    return {"title": title, "text": text,
            "publish_date": str(pub_date) if pub_date else "", "category": category}


def parse_samakal(soup: BeautifulSoup, url: str) -> dict | None:
    title_tag = soup.find("h1") or soup.find("meta", property="og:title")
    title = (title_tag.get("content") if title_tag and title_tag.name == "meta"
             else title_tag.get_text(strip=True) if title_tag else "")
    body = soup.find("div", class_=re.compile(r"detail|article|content|story", re.I)) or \
           soup.find("article")
    text = " ".join(p.get_text(" ", strip=True) for p in (body.find_all("p") if body else []))
    pub_date = _extract_pub_date(soup)
    parts = urlparse(url).path.strip("/").split("/")
    category = parts[0] if parts else "national"
    return {"title": title, "text": text,
            "publish_date": str(pub_date) if pub_date else "", "category": category}


def parse_jugantor(soup: BeautifulSoup, url: str) -> dict | None:
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""
    body = soup.find("div", class_=re.compile(r"news|article|detail|content", re.I)) or \
           soup.find("div", id=re.compile(r"content|article", re.I))
    text = " ".join(p.get_text(" ", strip=True) for p in (body.find_all("p") if body else []))
    pub_date = _extract_pub_date(soup)
    parts = urlparse(url).path.strip("/").split("/")
    return {"title": title, "text": text,
            "publish_date": str(pub_date) if pub_date else "",
            "category": parts[0] if parts else "national"}


def parse_ittefaq(soup: BeautifulSoup, url: str) -> dict | None:
    title_tag = soup.find("h1") or soup.find("meta", property="og:title")
    title = (title_tag.get("content") if title_tag and title_tag.name == "meta"
             else title_tag.get_text(strip=True) if title_tag else "")
    body = soup.find("div", class_="details-body") or \
           soup.find("div", class_=re.compile(r"detail|news|article|body", re.I))
    text = " ".join(p.get_text(" ", strip=True) for p in (body.find_all("p") if body else []))
    pub_date = _extract_pub_date(soup)
    parts = urlparse(url).path.strip("/").split("/")
    return {"title": title, "text": text,
            "publish_date": str(pub_date) if pub_date else "",
            "category": parts[0] if parts else "national"}


def parse_generic_news(soup: BeautifulSoup, url: str) -> dict | None:
    title_tag = soup.find("h1") or soup.find("meta", property="og:title")
    title = (title_tag.get("content") if title_tag and title_tag.name == "meta"
             else title_tag.get_text(strip=True) if title_tag else "")
    text = _generic_body(soup)
    pub_date = _extract_pub_date(soup)
    parts = urlparse(url).path.strip("/").split("/")
    return {"title": title, "text": text,
            "publish_date": str(pub_date) if pub_date else "",
            "category": parts[0] if parts else "national"}


def parse_shomoyeralo(soup: BeautifulSoup, url: str) -> dict | None:
    title_tag = (soup.find("h1") or
                 soup.find("h2", class_=re.compile(r"title|heading", re.I)) or
                 soup.find("meta", property="og:title"))
    title = (title_tag.get("content") if title_tag and title_tag.name == "meta"
             else title_tag.get_text(strip=True) if title_tag else "")
    body = soup.find("div", class_=re.compile(r"details?|body|content|news", re.I)) or \
           soup.find("article")
    text = " ".join(p.get_text(" ", strip=True) for p in (body.find_all("p") if body else []))
    pub_date = _extract_pub_date(soup)
    return {"title": title, "text": text,
            "publish_date": str(pub_date) if pub_date else "", "category": "national"}


def parse_bd_pratidin(soup: BeautifulSoup, url: str) -> dict | None:
    title_tag = soup.find("h1") or soup.find("meta", property="og:title")
    title = (title_tag.get("content") if title_tag and title_tag.name == "meta"
             else title_tag.get_text(strip=True) if title_tag else "")
    body = (soup.find("div", class_=re.compile(r"details?.body|news.details|article.body", re.I)) or
            soup.find("div", class_=re.compile(r"detail|content|story", re.I)) or
            soup.find("article"))
    text = " ".join(p.get_text(" ", strip=True) for p in (body.find_all("p") if body else []))
    pub_date = _extract_pub_date(soup)
    parts = urlparse(url).path.strip("/").split("/")
    return {"title": title, "text": text,
            "publish_date": str(pub_date) if pub_date else "",
            "category": parts[0] if parts else "national"}


# ── Earki.co article parser ───────────────────────────────────────────────────

def parse_earki(soup: BeautifulSoup, url: str) -> dict | None:
    """
    Parse a single earki.co article.
    Structure:
      - Title:  <h1> or og:title meta
      - Author: <a href="/author/...">
      - Body:   The big text block between the header nav and the "আরও" section.
                We look for the main <div> containing <p> tags with the story text.
      - Date:   earki rarely exposes a machine-readable date; we try OG/JSON-LD.
    """
    # Title
    title_tag = soup.find("h1") or soup.find("meta", property="og:title")
    title = ""
    if title_tag:
        if title_tag.name == "meta":
            title = title_tag.get("content", "").strip()
        else:
            title = title_tag.get_text(strip=True)

    if not title:
        # Fallback: page <title>
        t = soup.find("title")
        if t:
            title = t.get_text(strip=True).split(" - ")[0].strip()

    # Date
    pub_date = _extract_pub_date(soup)

    # Body — earki puts body text inside <p> siblings after the breadcrumb/author area.
    # Strategy: grab ALL <p> text from the page body, skip boilerplate (nav/footer).
    # We identify the article text region by looking for the large group of <p> tags.
    body_text = ""

    # Try common content wrappers first
    for cls_pat in [r"article.?content|post.?content|entry.?content",
                    r"article.?body|story.?body|content",
                    r"article"]:
        div = soup.find("div", class_=re.compile(cls_pat, re.I))
        if div:
            paras = [p.get_text(" ", strip=True) for p in div.find_all("p") if len(p.get_text(strip=True)) > 20]
            if paras:
                body_text = " ".join(paras)
                break

    # Fallback: collect all <p> tags with meaningful text, skip very short ones
    if not body_text:
        all_paras = [
            p.get_text(" ", strip=True)
            for p in soup.find_all("p")
            if len(p.get_text(strip=True)) > 30
        ]
        # Drop the last few boilerplate paragraphs (footer/nav text)
        body_text = " ".join(all_paras)

    # Determine category from URL path segment 1 (humor/satire/news/interview)
    path_parts = urlparse(url).path.strip("/").split("/")
    category = path_parts[0] if path_parts else "humor"

    return {
        "title":        title,
        "text":         body_text,
        "publish_date": str(pub_date) if pub_date else "",
        "category":     category,
    }


# ── Disabled fact-check parsers (kept for future use) ─────────────────────────

def _parse_factcheck_base(soup: BeautifulSoup, url: str) -> dict | None:
    title_tag = soup.find("h1") or soup.find("meta", property="og:title")
    title = (title_tag.get("content") if title_tag and title_tag.name == "meta"
             else title_tag.get_text(strip=True) if title_tag else "")
    body = (soup.find("div", class_=re.compile(r"entry.content|post.content|article.body", re.I)) or
            soup.find("div", class_=re.compile(r"entry|content|article", re.I)) or
            soup.find("article"))
    text = " ".join(p.get_text(" ", strip=True) for p in (body.find_all("p") if body else []))
    pub_date = _extract_pub_date(soup)
    return {"title": title, "text": text,
            "publish_date": str(pub_date) if pub_date else "", "category": "fact-check"}


def parse_rumorscanner(soup, url):  return _parse_factcheck_base(soup, url)
def parse_factwatch(soup, url):     return _parse_factcheck_base(soup, url)
def parse_jachai(soup, url):        return _parse_factcheck_base(soup, url)
def parse_rumorinspector(soup, url): return _parse_factcheck_base(soup, url)
def parse_boombd(soup, url):        return _parse_factcheck_base(soup, url)


# Parser dispatch table
PARSERS = {
    "prothomalo":    parse_prothomalo,
    "samakal":       parse_samakal,
    "jugantor":      parse_jugantor,
    "ittefaq":       parse_ittefaq,
    "generic_news":  parse_generic_news,
    "shomoyeralo":   parse_shomoyeralo,
    "bd_pratidin":   parse_bd_pratidin,
    "earki":         parse_earki,
    # fact-check (disabled but parsers still registered)
    "rumorscanner":  parse_rumorscanner,
    "factwatch":     parse_factwatch,
    "jachai":        parse_jachai,
    "rumorinspector": parse_rumorinspector,
    "boombd":        parse_boombd,
}


# =============================================================================
#  MAIN SCRAPE LOOP
# =============================================================================

def scrape(max_articles: int, start: date, end: date):
    log.info("=" * 68)
    log.info(f"▶ SCRAPE START  {datetime.now().strftime('%Y-%m-%d %H:%M')}  "
             f"range={start}→{end}  max={max_articles}")
    log.info("=" * 68)

    visited      = load_visited()
    seen_hashes  = load_seen_hashes()
    state        = load_state()
    collected    = []
    total_new    = 0
    total_skip   = 0
    source_counts: dict[str, int] = {}

    # Only include active sources (skip disabled ones)
    active_sources = [s for s in SOURCES if s["label"] != "disabled"]
    source_counts  = {s["name"]: 0 for s in active_sources}

    # ── ID counter ────────────────────────────────────────────────────────────
    _id_counter = [get_next_id()]
    def next_id():
        v = _id_counter[0]
        _id_counter[0] += 1
        return v

    # ── Build one lazy generator per active source ─────────────────────────
    generators = [
        {"source": src, "gen": get_urls_for_source(src, start, end), "active": True}
        for src in active_sources
    ]

    while total_new < max_articles:
        active = [g for g in generators if g["active"]]
        if not active:
            log.info("All sources exhausted.")
            break

        # Pick a random active source
        g = random.choice(active)
        src = g["source"]

        try:
            url = next(g["gen"])
        except StopIteration:
            g["active"] = False
            continue

        if url in visited:
            total_skip += 1
            continue

        visited.add(url)

        parser_fn = PARSERS.get(src["parser"])
        if not parser_fn:
            g["active"] = False
            continue

        polite_sleep()
        soup = fetch(url)
        if not soup:
            continue

        try:
            data = parser_fn(soup, url)
        except Exception as exc:
            log.error(f"  Parser error [{url}]: {exc}")
            continue

        if not data:
            continue

        title = data.get("title", "").strip()
        text  = data.get("text",  "").strip()

        if not title:
            continue
        if len(text.split()) < MIN_WORD_COUNT:
            log.debug(f"  Skip (short {len(text.split())} words): {url}")
            continue

        # Date filter (skip if outside range; accept if no date found)
        pub_date_str = data.get("publish_date", "")
        pub_date_obj = parse_date_str(pub_date_str) if pub_date_str else None
        if pub_date_obj and not in_date_range(pub_date_obj, start, end):
            log.debug(f"  Skip (date {pub_date_obj} out of range): {url}")
            continue

        # Content-hash dedup
        chash = content_hash(title, text)
        if chash in seen_hashes:
            total_skip += 1
            log.debug(f"  Skip (duplicate hash): {url}")
            continue
        seen_hashes.add(chash)

        # ── Build output row ──────────────────────────────────────────────
        row = {
            "id":           next_id(),
            "title":        title,
            "text":         text,
            "source":       src["name"],
            "publish_date": pub_date_str,
            "category":     data.get("category", src.get("category", "")),
            "label":        src["label"],   # "real" or "fake"
            "url":          url,
            "content_hash": chash,
        }

        collected.append(row)
        total_new  += 1
        source_counts[src["name"]] = source_counts.get(src["name"], 0) + 1
        log.info(f"  [{total_new}/{max_articles}] ({src['label']}) [{src['name']}] {title[:60]}...")

        # Batch save
        if len(collected) >= BATCH_SAVE_EVERY:
            append_to_csv(collected)
            save_visited(visited)
            collected.clear()
            log.info(f"  💾 Batch saved | total_new={total_new}")

    # Final flush
    if collected:
        append_to_csv(collected)
    save_visited(visited)

    state["total_collected"] = state.get("total_collected", 0) + total_new
    save_state(state)

    # ── Summary ────────────────────────────────────────────────────────────
    from collections import Counter
    label_counts: Counter = Counter()
    if os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, "r", encoding="utf-8-sig") as _f:
                for row in csv.DictReader(_f):
                    label_counts[row.get("label", "?")] += 1
        except Exception:
            pass

    log.info("=" * 68)
    log.info("✅  SCRAPING COMPLETE")
    log.info(f"   New articles   : {total_new}")
    log.info(f"   Skipped (dup)  : {total_skip}")
    log.info(f"   Total all runs : {state['total_collected']}")
    log.info("   ── Label breakdown (CSV total) ──")
    for lbl in ["real", "fake"]:
        log.info(f"      {lbl:8s}: {label_counts.get(lbl, 0)}")
    log.info("   ── Per-source new (this run) ──")
    for name, cnt in source_counts.items():
        if cnt:
            log.info(f"      {name}: {cnt}")
    log.info(f"   CSV  : {CSV_FILE}")
    log.info("=" * 68)

    print(f"\n{'='*68}")
    print("  ✅  DONE")
    print(f"  New this run : {total_new}   Skipped : {total_skip}")
    print(f"  real={label_counts.get('real', 0)}   fake={label_counts.get('fake', 0)}")
    print(f"  Saved to: {CSV_FILE}")
    print(f"{'='*68}\n")


# =============================================================================
#  CLI
# =============================================================================

def main():
    ap = argparse.ArgumentParser(
        description="Bangla News Dataset Scraper v4  —  real / fake (2 labels)"
    )
    ap.add_argument("--max_articles", type=int, default=DEFAULT_MAX,
                    help=f"Max articles per run (default {DEFAULT_MAX})")
    ap.add_argument("--start_date", type=str, default=str(DEFAULT_START),
                    help=f"Start date YYYY-MM-DD (default {DEFAULT_START})")
    ap.add_argument("--end_date", type=str, default=str(DEFAULT_END),
                    help=f"End date YYYY-MM-DD (default today)")
    ap.add_argument("--fresh", action="store_true",
                    help="Delete existing CSV, visited list and state before starting")
    args = ap.parse_args()

    if args.fresh:
        for f in [CSV_FILE, VISITED_FILE, STATE_FILE]:
            if os.path.exists(f):
                os.remove(f)
                log.info(f"  🗑  Deleted {f}")

    try:
        start = date.fromisoformat(args.start_date)
        end   = date.fromisoformat(args.end_date)
    except ValueError as e:
        print(f"Invalid date: {e}")
        raise SystemExit(1)

    if end < start:
        print("Error: end_date must be >= start_date")
        raise SystemExit(1)

    scrape(max_articles=args.max_articles, start=start, end=end)


if __name__ == "__main__":
    main()
