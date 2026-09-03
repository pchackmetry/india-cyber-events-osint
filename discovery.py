import re
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote, urlparse

from sources import INDIAN_LOCATIONS, CYBERSECURITY_KEYWORDS

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    )
}

RSS_SEARCHES = [
    "cybersecurity event India",
    "cyber security event India",
    "infosec event India",
    "cybersecurity meetup India",
    "cyber security meetup India",
    "cybersecurity conference India",
    "cybersecurity workshop India",
    "cybersecurity CTF India",
    "security meetup India",
    "security conference India",
    "OWASP India event",
    "Null India cybersecurity meetup",
    "BSides India cybersecurity",
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
]

EVENT_WORDS = [
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
]


def search_google_news(query):
    """Search Google News RSS without an API key."""
    url = (
        "https://news.google.com/rss/search?"
        f"q={quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    )

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"❌ RSS search failed: {error}")
        return []

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as error:
        print(f"❌ RSS parsing failed: {error}")
        return []

    results = []

    for item in root.findall(".//item"):
        title = item.findtext("title", default="").strip()
        link = item.findtext("link", default="").strip()
        description = item.findtext("description", default="").strip()
        pub_date = item.findtext("pubDate", default="").strip()

        if not title or not link:
            continue

        results.append({
            "title": title,
            "url": link,
            "snippet": description,
            "published": pub_date,
        })

    return results


def clean_html(text):
    return re.sub(r"<[^>]+>", " ", text).strip()


def is_cybersecurity_event(title, snippet):
    text = f"{title} {snippet}".lower()
    text = clean_html(text)

    cyber_signal = any(
        keyword.lower() in text
        for keyword in CYBERSECURITY_KEYWORDS
    )

    if not cyber_signal:
        return False

    event_signal = any(
        word in text
        for word in EVENT_WORDS
    )

    return event_signal


def detect_location(text):
    text_lower = text.lower()

    aliases = {
        "bangalore": "Bengaluru",
        "bengaluru": "Bengaluru",
        "bombay": "Mumbai",
        "mumbai": "Mumbai",
        "calcutta": "Kolkata",
        "madras": "Chennai",
        "gurgaon": "Gurugram",
        "gurugram": "Gurugram",
        "new delhi": "Delhi",
        "delhi": "Delhi",
    }

    for alias, location in aliases.items():
        if alias in text_lower:
            return location

    for location in INDIAN_LOCATIONS:
        if location.lower() in text_lower:
            return location

    online_words = [
        "online",
        "virtual",
        "remote",
        "webinar",
        "online event",
    ]

    if any(word in text_lower for word in online_words):
        return "Online"

    india_words = [
        "india",
        "indian",
        "india-based",
    ]

    if any(word in text_lower for word in india_words):
        return "India"

    return "Unknown"


def get_domain(url):
    try:
        domain = urlparse(url).netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain
    except Exception:
        return ""


def source_score(url):
    domain = get_domain(url)

    trusted_domains = {
        "owasp.org": 30,
        "null.community": 30,
        "securitybsides.com": 30,
        "meetup.com": 20,
        "eventbrite.com": 20,
        "lu.ma": 20,
        "github.com": 15,
        "linkedin.com": 15,
    }

    for trusted_domain, score in trusted_domains.items():
        if domain == trusted_domain:
            return score

        if domain.endswith("." + trusted_domain):
            return score

    return 5


def calculate_score(event):
    score = 40

    score += source_score(event["url"])

    if event["location"] != "Unknown":
        score += 5

    if event["location"] == "Online":
        score += 5

    if len(event["title"]) >= 20:
        score += 5

    if len(event["snippet"]) >= 100:
        score += 5

    return min(score, 100)


def discover_events():
    print("========================================")
    print("🇮🇳 INDIA CYBERSECURITY EVENT DISCOVERY")
    print("========================================")
    print()

    discovered = []

    print(f"🔎 Running {len(RSS_SEARCHES)} RSS searches")
    print()

    for index, query in enumerate(RSS_SEARCHES, start=1):

        print(f"[{index}/{len(RSS_SEARCHES)}] Searching:")
        print(f"   {query}")

        results = search_google_news(query)

        print(f"   Results: {len(results)}")

        for result in results:

            title = result["title"]
            snippet = clean_html(result["snippet"])

            if not is_cybersecurity_event(title, snippet):
                continue

            combined_text = f"{title} {snippet}"

            location = detect_location(combined_text)

            # Ignore clearly non-India results.
            if location == "Unknown":
                continue

            event = {
                "title": title,
                "url": result["url"],
                "snippet": snippet,
                "published": result["published"],
                "location": location,
                "source": get_domain(result["url"]),
            }

            event["confidence"] = calculate_score(event)

            discovered.append(event)

    # Deduplicate URLs.
    unique_events = {}

    for event in discovered:

        url = event["url"].split("#")[0].rstrip("/")

        if url not in unique_events:
            unique_events[url] = event

    events = list(unique_events.values())

    # Sort highest confidence first.
    events.sort(
        key=lambda event: event["confidence"],
        reverse=True
    )

    print()
    print("========================================")
    print(f"🔎 DISCOVERED EVENTS: {len(events)}")
    print("========================================")

    for number, event in enumerate(events, start=1):

        print()
        print(f"{number}. {event['title']}")
        print(f"   📍 Location: {event['location']}")
        print(f"   ⭐ Confidence: {event['confidence']}/100")
        print(f"   🌐 Source: {event['source']}")
        print(f"   📅 Published: {event['published']}")
        print(f"   🔗 {event['url']}")

    return events


if __name__ == "__main__":
    discover_events()
