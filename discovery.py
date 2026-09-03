import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse

from sources import INDIAN_LOCATIONS, CYBERSECURITY_KEYWORDS


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    )
}


# ============================================================
# SEARCH
# ============================================================

def search_web(query):
    """
    Search DuckDuckGo public HTML results.
    No paid API required.
    """

    url = (
        "https://html.duckduckgo.com/html/"
        f"?q={quote(query)}"
    )

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"❌ Search failed: {error}")
        return []

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    results = []

    for result in soup.select(".result"):

        title_element = result.select_one(
            ".result__title"
        )

        link_element = result.select_one(
            ".result__a"
        )

        snippet_element = result.select_one(
            ".result__snippet"
        )

        if not title_element or not link_element:
            continue

        title = title_element.get_text(
            " ",
            strip=True
        )

        url = link_element.get("href")

        snippet = ""

        if snippet_element:
            snippet = snippet_element.get_text(
                " ",
                strip=True
            )

        if not url:
            continue

        results.append({
            "title": title,
            "url": url,
            "snippet": snippet
        })

    return results


# ============================================================
# SEARCH QUERY GENERATOR
# ============================================================

def generate_queries():

    queries = []

    # --------------------------------------------------------
    # INDIA-WIDE SEARCHES
    # --------------------------------------------------------

    queries.extend([
        '"cybersecurity" event India',
        '"cyber security" event India',
        '"information security" event India',
        '"infosec" event India',
        '"cybersecurity meetup" India',
        '"cyber security meetup" India',
        '"cybersecurity conference" India',
        '"cybersecurity workshop" India',
        '"cybersecurity CTF" India',
        '"security meetup" India',
        '"security conference" India'
    ])

    # --------------------------------------------------------
    # COMMUNITY SEARCHES
    # --------------------------------------------------------

    queries.extend([
        'site:owasp.org/events India cybersecurity',
        'site:owasp.org "Hyderabad" security',
        'site:owasp.org "Bengaluru" security',
        'site:owasp.org "Mumbai" security',
        'site:owasp.org "Pune" security',
        'site:owasp.org "Chennai" security',

        'site:null.community India cybersecurity',
        'site:securitybsides.com India',

        'site:lu.ma cybersecurity India',
        'site:meetup.com cybersecurity India',
        'site:eventbrite.com cybersecurity India'
    ])

    # --------------------------------------------------------
    # LOCATION SEARCHES
    # --------------------------------------------------------

    for location in INDIAN_LOCATIONS:

        queries.extend([
            f'"cybersecurity" event "{location}"',
            f'"cyber security" meetup "{location}"',
            f'"infosec" meetup "{location}"',
            f'"cybersecurity conference" "{location}"',
            f'"cybersecurity workshop" "{location}"',
            f'"security meetup" "{location}"'
        ])

    # --------------------------------------------------------
    # TOPIC SEARCHES
    # --------------------------------------------------------

    topics = [
        "AppSec",
        "Cloud Security",
        "AI Security",
        "SOC",
        "DFIR",
        "OSINT",
        "Threat Intelligence",
        "Digital Forensics",
        "Incident Response",
        "Penetration Testing",
        "Ethical Hacking",
        "Bug Bounty",
        "VAPT",
        "GRC",
        "IAM",
        "Network Security",
        "CTF",
        "Malware"
    ]

    for topic in topics:

        queries.extend([
            f'"{topic}" event India',
            f'"{topic}" meetup India',
            f'"{topic}" conference India'
        ])

    # Remove duplicate queries
    return list(
        dict.fromkeys(queries)
    )


# ============================================================
# EVENT KEYWORD FILTER
# ============================================================

def is_possible_event(title, snippet):

    text = (
        f"{title} {snippet}"
    ).lower()

    # Cybersecurity signal
    cyber_signal = any(
        keyword.lower() in text
        for keyword in CYBERSECURITY_KEYWORDS
    )

    if not cyber_signal:
        return False

    # Event signal
    event_words = [
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
        "talk"
    ]

    return any(
        word in text
        for word in event_words
    )


# ============================================================
# LOCATION DETECTION
# ============================================================

def detect_location(text):

    text_lower = text.lower()

    for location in INDIAN_LOCATIONS:

        if location.lower() in text_lower:

            return location

    # Common location aliases
    aliases = {
        "bangalore": "Bengaluru",
        "bengaluru": "Bengaluru",
        "bombay": "Mumbai",
        "calcutta": "Kolkata",
        "madras": "Chennai",
        "gurgaon": "Gurugram",
        "new delhi": "Delhi"
    }

    for alias, location in aliases.items():

        if alias in text_lower:
            return location

    if "online" in text_lower:
        return "Online"

    if "virtual" in text_lower:
        return "Online"

    return "India"


# ============================================================
# SOURCE DOMAIN
# ============================================================

def get_domain(url):

    try:

        domain = urlparse(url).netloc

        domain = domain.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:

        return ""


# ============================================================
# SOURCE RELIABILITY
# ============================================================

def source_score(url):

    domain = get_domain(url)

    trusted_domains = {

        "owasp.org": 30,
        "null.community": 30,
        "securitybsides.com": 30,

        "meetup.com": 20,
        "eventbrite.com": 20,
        "lu.ma": 20,

        "linkedin.com": 15
    }

    for trusted_domain, score in trusted_domains.items():

        if domain == trusted_domain:
            return score

        if domain.endswith("." + trusted_domain):
            return score

    return 5


# ============================================================
# EVENT CONFIDENCE
# ============================================================

def calculate_initial_score(event):

    score = 40

    score += source_score(
        event["url"]
    )

    if event["location"] != "India":
        score += 5

    if event["location"] == "Online":
        score += 5

    if len(event["title"]) > 10:
        score += 5

    if len(event["snippet"]) > 50:
        score += 5

    return min(score, 100)


# ============================================================
# DISCOVERY
# ============================================================

def discover_events():

    queries = generate_queries()

    print(
        f"🔎 Generated {len(queries)} search queries"
    )

    discovered = []

    # Initial free scan limit
    # We will increase this after testing.
    scan_queries = queries[:40]

    for index, query in enumerate(
        scan_queries,
        start=1
    ):

        print()
        print(
            f"[{index}/{len(scan_queries)}] "
            f"Searching:"
        )

        print(query)

        results = search_web(query)

        print(
            f"   Results: {len(results)}"
        )

        for result in results:

            title = result["title"]

            snippet = result["snippet"]

            if not is_possible_event(
                title,
                snippet
            ):
                continue

            combined_text = (
                f"{title} {snippet}"
            )

            location = detect_location(
                combined_text
            )

            event = {
                "title": title,
                "url": result["url"],
                "snippet": snippet,
                "location": location,
                "source": get_domain(
                    result["url"]
                ),
                "search_query": query
            }

            event["confidence"] = (
                calculate_initial_score(
                    event
                )
            )

            discovered.append(event)

    # ========================================================
    # DEDUPLICATION
    # ========================================================

    unique_events = {}

    for event in discovered:

        url = event["url"].split("#")[0]

        if url not in unique_events:

            unique_events[url] = event

    events = list(
        unique_events.values()
    )

    # ========================================================
    # SORT BY CONFIDENCE
    # ========================================================

    events.sort(
        key=lambda x: x["confidence"],
        reverse=True
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    print()
    print(
        "========================================"
    )

    print(
        f"🔎 DISCOVERED EVENTS: {len(events)}"
    )

    print(
        "========================================"
    )

    for number, event in enumerate(
        events,
        start=1
    ):

        print()
        print(
            f"{number}. {event['title']}"
        )

        print(
            f"   📍 {event['location']}"
        )

        print(
            f"   ⭐ Confidence: "
            f"{event['confidence']}/100"
        )

        print(
            f"   🌐 {event['source']}"
        )

        print(
            f"   🔗 {event['url']}"
        )

    return events


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    discover_events()
