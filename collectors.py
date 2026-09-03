import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
}

TIMEOUT = 20


@dataclass
class Candidate:
    title: str
    url: str
    source: str


# Direct public event/community sources.
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


CYBER_KEYWORDS = [
    "cyber",
    "security",
    "cybersecurity",
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


def fetch_page(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
        )

        if response.status_code != 200:
            print(f"   HTTP {response.status_code}")
            return None

        return response.text

    except Exception as e:
        print(f"   ERROR: {e}")
        return None


def is_relevant(title, url):
    text = f"{title} {url}".lower()

    has_cyber = any(
        keyword in text
        for keyword in CYBER_KEYWORDS
    )

    has_event = any(
        keyword in text
        for keyword in EVENT_KEYWORDS
    )

    return has_cyber and has_event


def extract_links(html, base_url, source_name):
    soup = BeautifulSoup(html, "lxml")

    candidates = []

    for link in soup.find_all("a", href=True):

        title = link.get_text(" ", strip=True)
        href = link.get("href", "").strip()

        if not title or not href:
            continue

        url = urljoin(base_url, href)

        if not url.startswith("http"):
            continue

        if not is_relevant(title, url):
            continue

        candidates.append(
            Candidate(
                title=title,
                url=url,
                source=source_name,
            )
        )

    return candidates


def collect_from_source(source):
    print()
    print(f"🌐 SOURCE: {source['name']}")
    print(f"   URL: {source['url']}")

    html = fetch_page(source["url"])

    if not html:
        print("   ❌ Could not access source")
        return []

    candidates = extract_links(
        html,
        source["url"],
        source["name"],
    )

    print(f"   Candidates found: {len(candidates)}")

    return candidates


def collect_candidates():
    print("=" * 60)
    print("🔎 DIRECT EVENT SOURCE COLLECTION")
    print("=" * 60)

    all_candidates = []

    for source in SOURCES:
        candidates = collect_from_source(source)
        all_candidates.extend(candidates)

    # Deduplicate URLs
    unique = {}

    for candidate in all_candidates:
        normalized = candidate.url.rstrip("/")

        if normalized not in unique:
            unique[normalized] = candidate

    candidates = list(unique.values())

    print()
    print("=" * 60)
    print(f"✅ UNIQUE CANDIDATES: {len(candidates)}")
    print("=" * 60)

    for index, candidate in enumerate(candidates, start=1):
        print()
        print(f"[{index}] {candidate.title}")
        print(f"    Source: {candidate.source}")
        print(f"    URL: {candidate.url}")

    return candidates


if __name__ == "__main__":
    collect_candidates()
