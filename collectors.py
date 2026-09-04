from __future__ import annotations

import re
import requests

from bs4 import BeautifulSoup
from dataclasses import dataclass
from urllib.parse import quote, urljoin


# ============================================================
# CONFIGURATION
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}

TIMEOUT = 20


# ============================================================
# CANDIDATE MODEL
# ============================================================

@dataclass
class Candidate:
    title: str
    url: str
    source: str
    description: str = ""


# ============================================================
# INDIAN CITIES
# ============================================================

INDIAN_CITIES = [
    "Hyderabad",
    "Bengaluru",
    "Mumbai",
    "Pune",
    "Chennai",
    "Delhi",
    "Gurugram",
    "Noida",
    "Kolkata",
    "Kochi",
    "Ahmedabad",
    "Jaipur",
    "Chandigarh",
    "Bhubaneswar",
    "Lucknow",
    "Indore",
    "Coimbatore",
    "Visakhapatnam",
]


# ============================================================
# CYBERSECURITY TOPICS
# ============================================================

CYBER_TOPICS = [
    "cybersecurity",
    "cyber security",
    "information security",
    "infosec",
    "application security",
    "appsec",
    "cloud security",
    "ai security",
    "network security",
    "soc",
    "blue team",
    "red team",
    "penetration testing",
    "pentesting",
    "ethical hacking",
    "vapt",
    "vulnerability",
    "bug bounty",
    "digital forensics",
    "dfir",
    "incident response",
    "threat intelligence",
    "malware",
    "osint",
    "grc",
    "iam",
    "identity security",
    "ctf",
    "capture the flag",
    "owasp",
]


# ============================================================
# EVENT TYPES
# ============================================================

EVENT_TYPES = [
    "event",
    "meetup",
    "conference",
    "workshop",
    "webinar",
    "summit",
    "training",
    "seminar",
    "networking",
    "community",
    "ctf",
    "hackathon",
]


# ============================================================
# INVALID / NON-EVENT LINK SIGNALS
# ============================================================

INVALID_LINK_TEXT = {
    "global events",
    "regional events",
    "partner events",
    "all events",
    "upcoming events",
    "past events",
    "event calendar",
    "events calendar",
    "event listings",
    "events listings",
    "events directory",
    "event directory",
    "event archive",
    "events archive",
    "chapters",
    "all chapters",
    "find events",
    "browse events",
    "view all events",
    "see all events",
}

INVALID_FRAGMENT_NAMES = {
    "#global",
    "#partner",
    "#partners",
    "#regional",
    "#regional-events",
    "#global-events",
    "#upcoming",
    "#past",
    "#events",
    "#calendar",
}


# ============================================================
# PUBLIC DIRECT SOURCES
# ============================================================

DIRECT_SOURCES = [
    {
        "name": "OWASP Events",
        "url": "https://owasp.org/events/",
    },
    {
        "name": "OWASP Chapters",
        "url": "https://owasp.org/chapters/",
    },
    {
        "name": "Null Community",
        "url": "https://null.community/",
    },
    {
        "name": "BSides",
        "url": "https://www.securitybsides.com/",
    },
]


# ============================================================
# FETCH
# ============================================================

def fetch(url: str) -> str | None:

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True,
        )

        print(
            f"   HTTP {response.status_code} | "
            f"{len(response.content)} bytes"
        )

        if response.status_code != 200:
            return None

        return response.text

    except requests.RequestException as exc:

        print(
            f"   ❌ Request error: {exc}"
        )

        return None

    except Exception as exc:

        print(
            f"   ❌ Unexpected error: {exc}"
        )

        return None


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize(text: str) -> str:

    text = text.lower()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# INVALID LINK DETECTION
# ============================================================

def is_invalid_link(
    title: str,
    url: str,
) -> bool:

    clean_title = normalize(
        title
    )

    clean_url = (
        url.strip()
        .lower()
    )

    # --------------------------------------------------------
    # Reject fragment-only OWASP section links.
    # --------------------------------------------------------

    fragment = ""

    if "#" in clean_url:
        fragment = (
            "#"
            + clean_url.split(
                "#",
                1
            )[1]
        )

    if fragment in INVALID_FRAGMENT_NAMES:
        return True

    # --------------------------------------------------------
    # Reject known listing/index section names.
    # --------------------------------------------------------

    if clean_title in INVALID_LINK_TEXT:
        return True

    # --------------------------------------------------------
    # Reject obvious listing URLs.
    # --------------------------------------------------------

    listing_patterns = [
        r"/events/?$",
        r"/events/$",
        r"/events/#",
        r"/event/",
        r"/events\?",
        r"/search",
        r"/discover",
        r"/calendar",
        r"/categories",
        r"/archive",
        r"/directory",
        r"/chapters/?$",
    ]

    for pattern in listing_patterns:

        if re.search(
            pattern,
            clean_url,
            flags=re.IGNORECASE,
        ):
            return True

    return False


# ============================================================
# CYBER RELEVANCE
# ============================================================

def is_cyber_event(
    title: str,
    context: str = "",
) -> bool:

    text = normalize(
        f"{title} {context}"
    )

    has_cyber = any(
        topic.lower() in text
        for topic in CYBER_TOPICS
    )

    has_event = any(
        event.lower() in text
        for event in EVENT_TYPES
    )

    return (
        has_cyber
        and has_event
    )


# ============================================================
# LOCATION DETECTION
# ============================================================

def detect_location(
    text: str,
) -> str:

    normalized = normalize(
        text
    )

    for city in INDIAN_CITIES:

        if city.lower() in normalized:

            return city

        if city == "Bengaluru":

            if "bangalore" in normalized:

                return "Bengaluru"

    if "india" in normalized:

        return "India"

    if "online" in normalized:

        return "Online"

    if "virtual" in normalized:

        return "Online"

    return "Unknown"


# ============================================================
# SOURCE LINK EXTRACTION
# ============================================================

def extract_links(
    html: str,
    base_url: str,
    source_name: str,
) -> list[Candidate]:

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    candidates = []

    for link in soup.find_all(
        "a",
        href=True,
    ):

        title = link.get_text(
            " ",
            strip=True,
        )

        href = link.get(
            "href",
            "",
        ).strip()

        if not title:
            continue

        if not href:
            continue

        url = urljoin(
            base_url,
            href,
        )

        if not url.startswith(
            "http"
        ):
            continue

        # ----------------------------------------------------
        # IMPORTANT:
        # Reject source/index/section links BEFORE
        # cybersecurity detection.
        # ----------------------------------------------------

        if is_invalid_link(
            title,
            url,
        ):

            print(
                f"      ⏭️ Skipping listing/section: "
                f"{title} -> {url}"
            )

            continue

        # ----------------------------------------------------
        # Reject links that point back to the same page.
        # ----------------------------------------------------

        normalized_base = (
            base_url
            .split("#", 1)[0]
            .rstrip("/")
            .lower()
        )

        normalized_url = (
            url
            .split("#", 1)[0]
            .rstrip("/")
            .lower()
        )

        if normalized_url == normalized_base:

            print(
                f"      ⏭️ Skipping source page: "
                f"{title}"
            )

            continue

        # ----------------------------------------------------
        # Build nearby context.
        # ----------------------------------------------------

        parent_text = ""

        parent = link.parent

        if parent:

            parent_text = parent.get_text(
                " ",
                strip=True,
            )

        # Also inspect the closest useful container.
        container_text = ""

        for parent_level in (
            link.parent,
            link.parent.parent
            if link.parent
            else None,
        ):

            if parent_level:

                container_text = (
                    parent_level.get_text(
                        " ",
                        strip=True,
                    )
                )

                if len(container_text) > len(
                    parent_text
                ):

                    parent_text = (
                        container_text
                    )

        context = (
            f"{title} "
            f"{parent_text} "
            f"{url}"
        )

        # ----------------------------------------------------
        # Cybersecurity + event relevance.
        # ----------------------------------------------------

        if not is_cyber_event(
            title,
            context,
        ):

            continue

        location = detect_location(
            context
        )

        description = (
            f"Location signal: {location}"
        )

        candidates.append(
            Candidate(
                title=title,
                url=url,
                source=source_name,
                description=description,
            )
        )

    return candidates


# ============================================================
# DIRECT SOURCE COLLECTION
# ============================================================

def collect_direct_sources() -> list[Candidate]:

    print()
    print("=" * 60)
    print("🌐 DIRECT PUBLIC EVENT SOURCES")
    print("=" * 60)

    candidates = []

    for source in DIRECT_SOURCES:

        print()
        print(
            f"🔎 {source['name']}"
        )

        print(
            f"   {source['url']}"
        )

        html = fetch(
            source["url"]
        )

        if not html:

            print(
                "   ❌ Could not access source"
            )

            continue

        source_candidates = extract_links(
            html=html,
            base_url=source["url"],
            source_name=source["name"],
        )

        print(
            f"   Candidates: "
            f"{len(source_candidates)}"
        )

        candidates.extend(
            source_candidates
        )

    return candidates


# ============================================================
# CITY/TOPIC SEARCH PAGES
# ============================================================

SEARCH_TEMPLATES = [
    (
        "Eventbrite",
        "https://www.eventbrite.com/d/india/{query}/"
    ),
    (
        "Meetup",
        "https://www.meetup.com/find/?keywords={query}&source=EVENTS"
    ),
    (
        "Luma",
        "https://lu.ma/discover?q={query}"
    ),
]


# ============================================================
# SEARCH QUERIES
# ============================================================

def build_search_queries() -> list[str]:

    queries = []

    # General India searches.
    for topic in CYBER_TOPICS:

        queries.append(
            f"{topic} India event"
        )

    # City + cybersecurity.
    for city in INDIAN_CITIES:

        queries.append(
            f"cybersecurity {city}"
        )

        queries.append(
            f"cyber security {city} meetup"
        )

        queries.append(
            f"infosec {city} event"
        )

        queries.append(
            f"security conference {city}"
        )

        queries.append(
            f"security workshop {city}"
        )

        queries.append(
            f"CTF {city}"
        )

        queries.append(
            f"cybersecurity networking {city}"
        )

    # Community combinations.
    for city in INDIAN_CITIES:

        queries.append(
            f"OWASP {city}"
        )

        queries.append(
            f"Null security {city}"
        )

        queries.append(
            f"BSides {city}"
        )

    return list(
        dict.fromkeys(
            queries
        )
    )


# ============================================================
# SEARCH PAGE COLLECTION
# ============================================================

def collect_search_pages() -> list[Candidate]:

    print()
    print("=" * 60)
    print("🔎 CITY + TOPIC EVENT DISCOVERY")
    print("=" * 60)

    queries = build_search_queries()

    print(
        f"📋 Discovery queries: "
        f"{len(queries)}"
    )

    candidates = []

    max_queries = 80

    for number, query in enumerate(
        queries[:max_queries],
        start=1,
    ):

        print()
        print(
            f"[{number}/{min(len(queries), max_queries)}] "
            f"{query}"
        )

        encoded_query = quote(
            query
        )

        for source_name, template in (
            SEARCH_TEMPLATES
        ):

            search_url = template.format(
                query=encoded_query
            )

            print(
                f"   → {source_name}"
            )

            html = fetch(
                search_url
            )

            if not html:
                continue

            source_candidates = extract_links(
                html=html,
                base_url=search_url,
                source_name=source_name,
            )

            if source_candidates:

                print(
                    f"      Found: "
                    f"{len(source_candidates)}"
                )

                candidates.extend(
                    source_candidates
                )

    return candidates


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate(
    candidates: list[Candidate],
) -> list[Candidate]:

    unique = {}

    for candidate in candidates:

        url = (
            candidate.url
            .strip()
        )

        # Remove URL fragments for deduplication.
        url = url.split(
            "#",
            1
        )[0]

        url = url.rstrip("/")

        if not url:
            continue

        if is_invalid_link(
            candidate.title,
            candidate.url,
        ):
            continue

        if url not in unique:

            unique[url] = candidate

    return list(
        unique.values()
    )


# ============================================================
# MAIN COLLECTOR
# ============================================================

def collect_candidates() -> list[Candidate]:

    print("=" * 60)
    print("🇮🇳 INDIA CYBERSECURITY EVENT DISCOVERY")
    print("=" * 60)

    all_candidates = []

    # --------------------------------------------------------
    # 1. Direct community sources
    # --------------------------------------------------------

    direct_candidates = (
        collect_direct_sources()
    )

    all_candidates.extend(
        direct_candidates
    )

    # --------------------------------------------------------
    # 2. City + topic discovery
    # --------------------------------------------------------

    search_candidates = (
        collect_search_pages()
    )

    all_candidates.extend(
        search_candidates
    )

    # --------------------------------------------------------
    # 3. Deduplicate
    # --------------------------------------------------------

    candidates = deduplicate(
        all_candidates
    )

    # --------------------------------------------------------
    # 4. Final report
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        f"📦 RAW CANDIDATES: "
        f"{len(all_candidates)}"
    )
    print(
        f"✅ UNIQUE CANDIDATES: "
        f"{len(candidates)}"
    )
    print("=" * 60)

    for number, candidate in enumerate(
        candidates[:50],
        start=1,
    ):

        print()
        print(
            f"[{number}] "
            f"{candidate.title}"
        )

        print(
            f"    Source: "
            f"{candidate.source}"
        )

        print(
            f"    {candidate.description}"
        )

        print(
            f"    URL: "
            f"{candidate.url}"
        )

    if len(candidates) > 50:

        print()
        print(
            f"... and "
            f"{len(candidates) - 50} "
            f"additional candidates."
        )

    return candidates


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    collect_candidates()
