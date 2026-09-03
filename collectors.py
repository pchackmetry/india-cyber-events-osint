"""
Public-source collectors for India Cybersecurity Events OSINT.

This file only collects candidate event pages.
Verification, scoring, deduplication, and Telegram delivery
will be handled separately.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIG
# ============================================================

TIMEOUT = 20
DELAY = 1

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    )
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# ============================================================
# DATA MODEL
# ============================================================

@dataclass
class Candidate:
    title: str
    url: str
    source: str
    description: str = ""


# ============================================================
# URL HELPERS
# ============================================================

def normalize_url(url: str) -> str:
    """Remove fragments and trailing slash."""

    if not url:
        return ""

    return url.split("#")[0].rstrip("/")


def domain(url: str) -> str:
    """Return hostname."""

    try:
        value = url.split("//", 1)[-1]
        value = value.split("/", 1)[0]
        value = value.split(":", 1)[0]

        if value.startswith("www."):
            value = value[4:]

        return value.lower()

    except Exception:
        return ""


# ============================================================
# HTTP
# ============================================================

def fetch(url: str) -> str:
    """Download a public webpage."""

    try:
        response = SESSION.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as error:
        print(f"   ⚠️ Failed: {url}")
        print(f"      {error}")

        return ""


# ============================================================
# TEXT
# ============================================================

def clean_text(text: str) -> str:
    """Normalize extracted text."""

    text = re.sub(r"\s+", " ", text or "")

    return text.strip()


# ============================================================
# GENERIC HTML EVENT EXTRACTION
# ============================================================

def extract_links(
    html: str,
    base_url: str,
    source_name: str,
) -> list[Candidate]:

    if not html:
        return []

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    candidates = []

    event_terms = (
        "event",
        "meetup",
        "conference",
        "workshop",
        "summit",
        "webinar",
        "ctf",
        "hackathon",
        "security",
        "cyber",
        "infosec",
        "owasp",
        "appsec",
    )

    for link in soup.find_all("a", href=True):

        title = clean_text(
            link.get_text(" ", strip=True)
        )

        href = link.get("href", "").strip()

        if not title or not href:
            continue

        full_url = normalize_url(
            urljoin(base_url, href)
        )

        if not full_url.startswith("http"):
            continue

        combined = (
            f"{title} {full_url}"
        ).lower()

        if not any(
            term in combined
            for term in event_terms
        ):
            continue

        candidates.append(
            Candidate(
                title=title,
                url=full_url,
                source=source_name,
            )
        )

    return candidates


# ============================================================
# GOOGLE NEWS RSS
# ============================================================

def google_news(
    query: str,
) -> list[Candidate]:

    url = (
        "https://news.google.com/rss/search?"
        f"q={quote(query)}"
        "&hl=en-IN"
        "&gl=IN"
        "&ceid=IN:en"
    )

    html = fetch(url)

    if not html:
        return []

    try:
        soup = BeautifulSoup(
            html,
            "xml",
        )

    except Exception:
        return []

    candidates = []

    for item in soup.find_all("item"):

        title = clean_text(
            item.title.get_text()
            if item.title
            else ""
        )

        link = clean_text(
            item.link.get_text()
            if item.link
            else ""
        )

        description = clean_text(
            item.description.get_text()
            if item.description
            else ""
        )

        if not title or not link:
            continue

        candidates.append(
            Candidate(
                title=title,
                url=normalize_url(link),
                source="Google News",
                description=description,
            )
        )

    return candidates


# ============================================================
# SEARCH QUERIES
# ============================================================

QUERIES = [
    "cybersecurity event India",
    "cyber security event India",
    "infosec event India",
    "cybersecurity meetup India",
    "security meetup India",
    "cybersecurity conference India",
    "cybersecurity workshop India",
    "cybersecurity CTF India",
    "cybersecurity hackathon India",
    "OWASP India event",
    "Null India meetup",
    "BSides India",
    "AppSec India event",
    "Cloud Security India event",
    "AI Security India event",
    "DFIR India event",
    "OSINT India event",
    "bug bounty India event",
    "VAPT India event",
    "GRC India event",
    "IAM India event",
    "network security India event",

    "cybersecurity event Hyderabad",
    "cybersecurity meetup Hyderabad",
    "OWASP Hyderabad",

    "cybersecurity event Bengaluru",
    "cybersecurity meetup Bengaluru",
    "OWASP Bengaluru",

    "cybersecurity event Mumbai",
    "cybersecurity meetup Mumbai",
    "OWASP Mumbai",

    "cybersecurity event Pune",
    "cybersecurity meetup Pune",
    "OWASP Pune",

    "cybersecurity event Chennai",
    "cybersecurity meetup Chennai",
    "OWASP Chennai",

    "cybersecurity event Delhi",
    "cybersecurity meetup Delhi",

    "cybersecurity event Noida",
    "cybersecurity event Gurugram",

    "cybersecurity webinar India",
    "online cybersecurity event India",
]


# ============================================================
# MAIN COLLECTOR
# ============================================================

def collect_candidates() -> list[Candidate]:

    print("=" * 60)
    print("🔎 COLLECTING CYBERSECURITY EVENT CANDIDATES")
    print("=" * 60)

    all_candidates = []

    for number, query in enumerate(
        QUERIES,
        start=1,
    ):

        print()
        print(
            f"[{number}/{len(QUERIES)}] "
            f"{query}"
        )

        results = google_news(query)

        print(
            f"   Found: {len(results)}"
        )

        all_candidates.extend(results)

        time.sleep(DELAY)

    # Deduplicate by URL.
    unique = {}

    for candidate in all_candidates:

        key = normalize_url(
            candidate.url
        )

        if not key:
            continue

        if key not in unique:
            unique[key] = candidate

    candidates = list(unique.values())

    print()
    print("=" * 60)
    print(
        f"📦 UNIQUE CANDIDATES: "
        f"{len(candidates)}"
    )
    print("=" * 60)

    for number, candidate in enumerate(
        candidates,
        start=1,
    ):

        print()
        print(
            f"{number}. {candidate.title}"
        )

        print(
            f"   Source: {candidate.source}"
        )

        print(
            f"   URL: {candidate.url}"
        )

    return candidates


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    candidates = collect_candidates()

    print()
    print(
        f"✅ Collection complete: "
        f"{len(candidates)} candidates"
    )
