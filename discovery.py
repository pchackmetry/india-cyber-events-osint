"""
India Cybersecurity Events OSINT Scanner

Current capabilities:
- Google News RSS discovery
- India/location detection
- Cybersecurity relevance filtering
- Event-type filtering
- URL normalization
- Deduplication
- Confidence scoring
- Clean console output

Designed to be extended later with:
- Direct source collectors
- Event-date extraction
- Registration verification
- Cancellation/postponement detection
- Telegram notifications
- Daily digest
- Telegram-history deduplication
"""

from __future__ import annotations

import html
import re
import sys
import time
import xml.etree.ElementTree as ET

from dataclasses import dataclass, asdict
from typing import Iterable
from urllib.parse import quote, urlparse, urlunparse

import requests

from sources import (
    CYBERSECURITY_KEYWORDS,
    INDIAN_LOCATIONS,
)


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "India Cybersecurity OSINT Scanner"

REQUEST_TIMEOUT = 20
REQUEST_DELAY_SECONDS = 1

MAX_RESULTS_PER_QUERY = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    )
}


# ============================================================
# SEARCH QUERIES
# ============================================================

RSS_SEARCHES = [
    # General India
    "cybersecurity event India",
    "cyber security event India",
    "information security event India",
    "infosec event India",
    "cybersecurity meetup India",
    "cyber security meetup India",
    "cybersecurity conference India",
    "cybersecurity workshop India",
    "cybersecurity CTF India",
    "security meetup India",
    "security conference India",
    "cybersecurity networking India",

    # Communities
    "OWASP India event",
    "Null India cybersecurity meetup",
    "BSides India cybersecurity",
    "security community India",
    "hacker meetup India",

    # Topics
    "AppSec event India",
    "Application Security event India",
    "Cloud Security event India",
    "AI Security event India",
    "SOC event India",
    "Blue Team event India",
    "Red Team event India",
    "DFIR event India",
    "digital forensics event India",
    "OSINT event India",
    "threat intelligence event India",
    "incident response event India",
    "bug bounty event India",
    "VAPT event India",
    "penetration testing event India",
    "ethical hacking event India",
    "GRC event India",
    "IAM event India",
    "network security event India",
    "malware event India",
    "CTF India",
    "cybersecurity hackathon India",

    # Hyderabad
    "cybersecurity event Hyderabad",
    "cybersecurity meetup Hyderabad",
    "infosec meetup Hyderabad",
    "OWASP Hyderabad event",
    "security meetup Hyderabad",

    # Bengaluru
    "cybersecurity event Bengaluru",
    "cybersecurity meetup Bengaluru",
    "infosec meetup Bengaluru",
    "OWASP Bengaluru event",
    "security meetup Bengaluru",

    # Mumbai
    "cybersecurity event Mumbai",
    "cybersecurity meetup Mumbai",
    "infosec meetup Mumbai",
    "OWASP Mumbai event",
    "security meetup Mumbai",

    # Pune
    "cybersecurity event Pune",
    "cybersecurity meetup Pune",
    "infosec meetup Pune",
    "OWASP Pune event",
    "security meetup Pune",

    # Chennai
    "cybersecurity event Chennai",
    "cybersecurity meetup Chennai",
    "infosec meetup Chennai",
    "OWASP Chennai event",
    "security meetup Chennai",

    # Delhi NCR
    "cybersecurity event Delhi",
    "cybersecurity meetup Delhi",
    "cybersecurity event Gurgaon",
    "cybersecurity event Gurugram",
    "cybersecurity event Noida",

    # Other cities
    "cybersecurity event Kolkata",
    "cybersecurity event Kochi",
    "cybersecurity event Ahmedabad",
    "cybersecurity event Jaipur",
    "cybersecurity event Chandigarh",
    "cybersecurity event Bhubaneswar",
    "cybersecurity event Lucknow",
    "cybersecurity event Indore",
    "cybersecurity event Coimbatore",
    "cybersecurity event Visakhapatnam",

    # Online
    "cybersecurity webinar India",
    "cybersecurity virtual event India",
    "online cybersecurity conference India",
    "online cybersecurity workshop India",
]


# ============================================================
# EVENT TYPES
# ============================================================

EVENT_WORDS = {
    "event",
    "meetup",
    "conference",
    "workshop",
    "summit",
    "webinar",
    "ctf",
    "hackathon",
    "networking",
    "seminar",
    "community",
    "session",
    "talk",
    "training",
    "bootcamp",
    "challenge",
}


# ============================================================
# LOCATION ALIASES
# ============================================================

LOCATION_ALIASES = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "bombay": "Mumbai",
    "mumbai": "Mumbai",
    "calcutta": "Kolkata",
    "kolkata": "Kolkata",
    "madras": "Chennai",
    "chennai": "Chennai",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "new delhi": "Delhi",
    "delhi": "Delhi",
    "noida": "Noida",
}


# ============================================================
# DATA MODEL
# ============================================================

@dataclass
class Event:
    title: str
    url: str
    snippet: str
    published: str
    location: str
    source: str
    confidence: int


# ============================================================
# HTTP SESSION
# ============================================================

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# ============================================================
# TEXT UTILITIES
# ============================================================

def clean_text(value: str) -> str:
    """
    Remove HTML and normalize whitespace.
    """
    if not value:
        return ""

    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_url(url: str) -> str:
    """
    Normalize URLs for better deduplication.
    """
    if not url:
        return ""

    try:
        parsed = urlparse(url)

        cleaned = parsed._replace(
            fragment="",
            query="",
        )

        normalized = urlunparse(cleaned)

        return normalized.rstrip("/")

    except ValueError:
        return url.strip()


def get_domain(url: str) -> str:
    """
    Return normalized domain.
    """
    try:
        domain = urlparse(url).netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except ValueError:
        return ""


# ============================================================
# GOOGLE NEWS RSS
# ============================================================

def search_google_news(query: str) -> list[dict]:
    """
    Search Google News RSS.

    No API key is required.
    """

    rss_url = (
        "https://news.google.com/rss/search?"
        f"q={quote(query)}"
        "&hl=en-IN"
        "&gl=IN"
        "&ceid=IN:en"
    )

    try:
        response = SESSION.get(
            rss_url,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"   ❌ RSS request failed: {error}")
        return []

    try:
        root = ET.fromstring(response.content)

    except ET.ParseError as error:
        print(f"   ❌ RSS parsing failed: {error}")
        return []

    results = []

    for item in root.findall(".//item")[:MAX_RESULTS_PER_QUERY]:

        title = clean_text(
            item.findtext("title", default="")
        )

        link = clean_text(
            item.findtext("link", default="")
        )

        description = clean_text(
            item.findtext("description", default="")
        )

        published = clean_text(
            item.findtext("pubDate", default="")
        )

        if not title or not link:
            continue

        results.append(
            {
                "title": title,
                "url": link,
                "snippet": description,
                "published": published,
            }
        )

    return results


# ============================================================
# RELEVANCE
# ============================================================

def contains_cybersecurity_signal(
    title: str,
    snippet: str,
) -> bool:

    text = f"{title} {snippet}".lower()

    return any(
        keyword.lower() in text
        for keyword in CYBERSECURITY_KEYWORDS
    )


def contains_event_signal(
    title: str,
    snippet: str,
) -> bool:

    text = f"{title} {snippet}".lower()

    return any(
        word in text
        for word in EVENT_WORDS
    )


def is_possible_event(
    title: str,
    snippet: str,
) -> bool:

    if not contains_cybersecurity_signal(
        title,
        snippet,
    ):
        return False

    if not contains_event_signal(
        title,
        snippet,
    ):
        return False

    return True


# ============================================================
# LOCATION DETECTION
# ============================================================

def detect_location(text: str) -> str:

    text_lower = text.lower()

    # Check explicit city aliases first.
    for alias, location in LOCATION_ALIASES.items():

        if alias in text_lower:
            return location

    # Check configured Indian locations.
    for location in INDIAN_LOCATIONS:

        if location.lower() in text_lower:
            return location

    # Online event detection.
    online_terms = [
        "online",
        "virtual",
        "remote",
        "webinar",
        "virtual event",
        "online event",
    ]

    if any(term in text_lower for term in online_terms):
        return "Online"

    # India-level event.
    india_terms = [
        "india",
        "indian",
        "india-based",
    ]

    if any(term in text_lower for term in india_terms):
        return "India"

    return "Unknown"


# ============================================================
# SOURCE SCORING
# ============================================================

TRUSTED_SOURCES = {
    "owasp.org": 30,
    "null.community": 30,
    "securitybsides.com": 30,
    "meetup.com": 20,
    "eventbrite.com": 20,
    "lu.ma": 20,
    "github.com": 15,
    "linkedin.com": 15,
}


def source_score(url: str) -> int:

    domain = get_domain(url)

    for trusted_domain, score in TRUSTED_SOURCES.items():

        if domain == trusted_domain:
            return score

        if domain.endswith("." + trusted_domain):
            return score

    return 5


# ============================================================
# CONFIDENCE SCORE
# ============================================================

def calculate_confidence(
    title: str,
    snippet: str,
    location: str,
    url: str,
) -> int:

    score = 35

    # Source reliability.
    score += source_score(url)

    # Location confidence.
    if location != "Unknown":
        score += 5

    if location == "Online":
        score += 5

    # Better titles.
    if len(title) >= 25:
        score += 5

    # Better descriptions.
    if len(snippet) >= 100:
        score += 5

    # Registration/event-related wording.
    combined = f"{title} {snippet}".lower()

    useful_terms = [
        "register",
        "registration",
        "rsvp",
        "tickets",
        "venue",
        "speaker",
        "speakers",
        "date",
    ]

    matched = sum(
        1
        for term in useful_terms
        if term in combined
    )

    score += min(matched * 2, 10)

    return min(score, 100)


# ============================================================
# EVENT CREATION
# ============================================================

def build_event(result: dict) -> Event | None:

    title = clean_text(result.get("title", ""))
    snippet = clean_text(result.get("snippet", ""))
    url = normalize_url(result.get("url", ""))

    if not title or not url:
        return None

    location = detect_location(
        f"{title} {snippet}"
    )

    if location == "Unknown":
        return None

    confidence = calculate_confidence(
        title=title,
        snippet=snippet,
        location=location,
        url=url,
    )

    return Event(
        title=title,
        url=url,
        snippet=snippet,
        published=result.get("published", ""),
        location=location,
        source=get_domain(url),
        confidence=confidence,
    )


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate_events(
    events: Iterable[Event],
) -> list[Event]:

    unique = {}

    for event in events:

        key = normalize_url(event.url)

        if not key:
            continue

        existing = unique.get(key)

        if existing is None:
            unique[key] = event
            continue

        # Keep the stronger record.
        if event.confidence > existing.confidence:
            unique[key] = event

    return list(unique.values())


# ============================================================
# DISCOVERY ENGINE
# ============================================================

def discover_events() -> list[Event]:

    print()
    print("=" * 60)
    print(f"🇮🇳 {APP_NAME}")
    print("=" * 60)
    print()

    print(
        f"🔎 Search queries: {len(RSS_SEARCHES)}"
    )

    print()

    discovered: list[Event] = []

    for index, query in enumerate(
        RSS_SEARCHES,
        start=1,
    ):

        print(
            f"[{index}/{len(RSS_SEARCHES)}] "
            f"Searching: {query}"
        )

        results = search_google_news(query)

        print(
            f"   Results returned: {len(results)}"
        )

        for result in results:

            title = clean_text(
                result.get("title", "")
            )

            snippet = clean_text(
                result.get("snippet", "")
            )

            if not is_possible_event(
                title,
                snippet,
            ):
                continue

            event = build_event(result)

            if event is not None:
                discovered.append(event)

        # Avoid hammering the public endpoint.
        time.sleep(REQUEST_DELAY_SECONDS)

    events = deduplicate_events(
        discovered
    )

    events.sort(
        key=lambda event: event.confidence,
        reverse=True,
    )

    print()
    print("=" * 60)
    print(
        f"🔎 DISCOVERED EVENTS: {len(events)}"
    )
    print("=" * 60)

    if not events:
        print()
        print(
            "⚠️ No matching events were discovered."
        )
        print(
            "The discovery sources may have returned "
            "no usable results."
        )

        return []

    for number, event in enumerate(
        events,
        start=1,
    ):

        print()
        print(
            f"{number}. {event.title}"
        )

        print(
            f"   📍 Location: {event.location}"
        )

        print(
            f"   ⭐ Confidence: "
            f"{event.confidence}/100"
        )

        print(
            f"   🌐 Source: {event.source}"
        )

        if event.published:
            print(
                f"   📅 Published: "
                f"{event.published}"
            )

        print(
            f"   🔗 {event.url}"
        )

    return events


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    try:

        events = discover_events()

        print()
        print(
            f"✅ Scanner finished. "
            f"Events found: {len(events)}"
        )

        return 0

    except KeyboardInterrupt:

        print()
        print("⚠️ Scanner interrupted.")

        return 130

    except Exception as error:

        print()
        print(
            f"❌ Unexpected scanner error: "
            f"{error}"
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())
