from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}

TIMEOUT = 20


@dataclass
class Candidate:
    title: str
    url: str
    source: str
    description: str = ""


# ============================================================
# DIRECT PUBLIC SOURCES
# ============================================================

SOURCES = [
    {
        "name": "OWASP Events",
        "url": "https://owasp.org/events/",
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
# RELEVANCE KEYWORDS
# ============================================================

CYBER_KEYWORDS = [
    "cyber",
    "cybersecurity",
    "cyber security",
    "information security",
    "infosec",
    "application security",
    "appsec",
    "cloud security",
    "ai security",
    "network security",
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
    "soc",
    "blue team",
    "red team",
    "grc",
    "iam",
    "identity security",
    "ctf",
    "capture the flag",
    "hackathon",
]


EVENT_KEYWORDS = [
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


INDIA_LOCATIONS = [
    "india",
    "hyderabad",
    "bengaluru",
    "bangalore",
    "mumbai",
    "pune",
    "chennai",
    "delhi",
    "gurugram",
    "gurgaon",
    "noida",
    "kolkata",
    "kochi",
    "ahmedabad",
    "jaipur",
    "chandigarh",
    "bhubaneswar",
    "lucknow",
    "indore",
    "coimbatore",
    "visakhapatnam",
]


# ============================================================
# FETCH PAGE
# ============================================================

def fetch_page(url: str) -> str | None:
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
        )

        print(
            f"   HTTP {response.status_code} | "
            f"{len(response.content)} bytes"
        )

        if response.status_code != 200:
            return None

        return response.text

    except requests.RequestException as exc:
        print(f"   ❌ Request error: {exc}")
        return None

    except Exception as exc:
        print(f"   ❌ Unexpected error: {exc}")
        return None


# ============================================================
# RELEVANCE CHECK
# ============================================================

def is_relevant(title: str, url: str) -> bool:
    text = f"{title} {url}".lower()

    has_cyber_keyword = any(
        keyword in text
        for keyword in CYBER_KEYWORDS
    )

    has_event_keyword = any(
        keyword in text
        for keyword in EVENT_KEYWORDS
    )

    return (
        has_cyber_keyword
        and has_event_keyword
    )


# ============================================================
# INDIA / ONLINE LOCATION CHECK
# ============================================================

def has_india_location(title: str, url: str) -> bool:
    text = f"{title} {url}".lower()

    return any(
        location in text
        for location in INDIA_LOCATIONS
    ) or "online" in text


# ============================================================
# EXTRACT LINKS
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

    candidates: list[Candidate] = []

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

        if not title or not href:
            continue

        url = urljoin(
            base_url,
            href,
        )

        if not url.startswith(
            "http"
        ):
            continue

        if not is_relevant(
            title,
            url,
        ):
            continue

        # Keep India/online events when
        # the information is visible in the link.
        location_match = has_india_location(
            title,
            url,
        )

        description = (
            "India/Online location signal detected."
            if location_match
            else ""
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
# COLLECT FROM ONE SOURCE
# ============================================================

def collect_from_source(
    source: dict,
) -> list[Candidate]:

    print()
    print("=" * 60)
    print(
        f"🌐 SOURCE: {source['name']}"
    )
    print(
        f"   URL: {source['url']}"
    )

    html = fetch_page(
        source["url"]
    )

    if not html:
        print(
            "   ❌ Source unavailable"
        )
        return []

    candidates = extract_links(
        html=html,
        base_url=source["url"],
        source_name=source["name"],
    )

    print(
        f"   Candidates found: "
        f"{len(candidates)}"
    )

    return candidates


# ============================================================
# MAIN COLLECTION
# ============================================================

def collect_candidates() -> list[Candidate]:

    print("=" * 60)
    print(
        "🔎 DIRECT EVENT SOURCE COLLECTION"
    )
    print("=" * 60)

    all_candidates: list[Candidate] = []

    for source in SOURCES:

        candidates = collect_from_source(
            source
        )

        all_candidates.extend(
            candidates
        )

    # --------------------------------------------------------
    # Deduplicate by normalized URL
    # --------------------------------------------------------

    unique_candidates: dict[
        str,
        Candidate
    ] = {}

    for candidate in all_candidates:

        normalized_url = (
            candidate.url
            .strip()
            .rstrip("/")
        )

        if normalized_url not in unique_candidates:
            unique_candidates[
                normalized_url
            ] = candidate

    candidates = list(
        unique_candidates.values()
    )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        f"✅ UNIQUE CANDIDATES: "
        f"{len(candidates)}"
    )
    print("=" * 60)

    for number, candidate in enumerate(
        candidates,
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
            f"    URL: "
            f"{candidate.url}"
        )

        if candidate.description:
            print(
                f"    Description: "
                f"{candidate.description}"
            )

    return candidates


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":
    collect_candidates()
