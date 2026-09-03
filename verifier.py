from __future__ import annotations

import re
import requests

from dataclasses import dataclass
from datetime import datetime, timezone
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}

TIMEOUT = 20


# ============================================================
# KEYWORDS
# ============================================================

CYBER_KEYWORDS = [
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
    "security operations",
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


ONLINE_KEYWORDS = [
    "online",
    "virtual",
    "remote",
    "zoom",
    "webinar",
    "virtual event",
]


REGISTRATION_KEYWORDS = [
    "register",
    "registration",
    "rsvp",
    "tickets",
    "book now",
    "sign up",
    "join event",
    "attend",
    "reserve",
]


# ============================================================
# VERIFICATION RESULT
# ============================================================

@dataclass
class VerificationResult:
    reachable: bool
    title: str
    text: str

    has_registration_signal: bool
    has_date_signal: bool
    has_future_date: bool
    has_location_signal: bool
    has_india_location: bool
    has_online_signal: bool
    has_cyber_signal: bool
    has_event_signal: bool

    detected_dates: list[str]


# ============================================================
# FETCH PAGE
# ============================================================

def fetch_page(url: str) -> str | None:

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True,
        )

        if response.status_code != 200:
            print(
                f"   ❌ HTTP {response.status_code}"
            )
            return None

        if not response.text:
            print("   ❌ Empty page")
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
# EXTRACT PAGE CONTENT
# ============================================================

def extract_page_content(
    html: str,
) -> tuple[str, str]:

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    # Remove unnecessary elements.
    for element in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
        ]
    ):
        element.decompose()

    title = ""

    if soup.title:
        title = soup.title.get_text(
            " ",
            strip=True,
        )

    text = soup.get_text(
        " ",
        strip=True,
    )

    # Normalize whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return title, text


# ============================================================
# KEYWORD CHECK
# ============================================================

def contains_keyword(
    text: str,
    keywords: list[str],
) -> bool:

    text_lower = text.lower()

    return any(
        keyword in text_lower
        for keyword in keywords
    )


# ============================================================
# DATE EXTRACTION
# ============================================================

def extract_dates(
    text: str,
) -> list[str]:

    patterns = [
        # 3 September 2026
        r"\b\d{1,2}\s+"
        r"(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+\d{4}\b",

        # September 3, 2026
        r"\b(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+\d{1,2},\s+\d{4}\b",

        # 03/09/2026 or 03-09-2026
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b",

        # 2026-09-03
        r"\b\d{4}-\d{2}-\d{2}\b",

        # Sep 3 2026
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        r"[a-z]*\s+\d{1,2},?\s+\d{4}\b",
    ]

    matches = []

    for pattern in patterns:

        found = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        matches.extend(found)

    # Remove duplicates.
    unique = []

    for date_text in matches:

        if date_text not in unique:
            unique.append(date_text)

    return unique


# ============================================================
# PARSE DATE
# ============================================================

def parse_date(
    date_text: str,
) -> datetime | None:

    formats = [
        "%d %B %Y",
        "%B %d, %Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%b %d %Y",
        "%b %d, %Y",
    ]

    for fmt in formats:

        try:
            parsed = datetime.strptime(
                date_text,
                fmt,
            )

            return parsed.replace(
                tzinfo=timezone.utc
            )

        except ValueError:
            continue

    return None


# ============================================================
# FUTURE DATE CHECK
# ============================================================

def has_future_date(
    detected_dates: list[str],
) -> bool:

    now = datetime.now(
        timezone.utc
    )

    for date_text in detected_dates:

        parsed = parse_date(
            date_text
        )

        if parsed and parsed.date() >= now.date():
            return True

    return False


# ============================================================
# LOCATION CHECK
# ============================================================

def location_signals(
    text: str,
) -> tuple[bool, bool, bool]:

    text_lower = text.lower()

    has_india = any(
        location in text_lower
        for location in INDIA_LOCATIONS
    )

    has_online = any(
        keyword in text_lower
        for keyword in ONLINE_KEYWORDS
    )

    return (
        has_india or has_online,
        has_india,
        has_online,
    )


# ============================================================
# REGISTRATION CHECK
# ============================================================

def registration_signal(
    soup: BeautifulSoup,
    text: str,
) -> bool:

    text_lower = text.lower()

    if any(
        keyword in text_lower
        for keyword in REGISTRATION_KEYWORDS
    ):
        return True

    for link in soup.find_all(
        "a",
        href=True,
    ):

        link_text = link.get_text(
            " ",
            strip=True,
        ).lower()

        href = link.get(
            "href",
            "",
        ).lower()

        combined = (
            f"{link_text} {href}"
        )

        if any(
            keyword in combined
            for keyword in REGISTRATION_KEYWORDS
        ):
            return True

    return False


# ============================================================
# VERIFY EVENT
# ============================================================

def verify_event(
    url: str,
) -> VerificationResult:

    print(
        f"   🔎 Verifying: {url}"
    )

    html = fetch_page(url)

    if not html:

        return VerificationResult(
            reachable=False,
            title="",
            text="",
            has_registration_signal=False,
            has_date_signal=False,
            has_future_date=False,
            has_location_signal=False,
            has_india_location=False,
            has_online_signal=False,
            has_cyber_signal=False,
            has_event_signal=False,
            detected_dates=[],
        )

    title, text = extract_page_content(
        html
    )

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    detected_dates = extract_dates(
        text
    )

    future_date = has_future_date(
        detected_dates
    )

    has_location, has_india, has_online = (
        location_signals(text)
    )

    has_registration = (
        registration_signal(
            soup,
            text,
        )
    )

    has_cyber = contains_keyword(
        f"{title} {text}",
        CYBER_KEYWORDS,
    )

    has_event = contains_keyword(
        f"{title} {text}",
        EVENT_KEYWORDS,
    )

    result = VerificationResult(
        reachable=True,
        title=title,
        text=text,
        has_registration_signal=has_registration,
        has_date_signal=bool(
            detected_dates
        ),
        has_future_date=future_date,
        has_location_signal=has_location,
        has_india_location=has_india,
        has_online_signal=has_online,
        has_cyber_signal=has_cyber,
        has_event_signal=has_event,
        detected_dates=detected_dates,
    )

    print(
        f"   Page title: {title}"
    )

    print(
        f"   Cyber signal: {has_cyber}"
    )

    print(
        f"   Event signal: {has_event}"
    )

    print(
        f"   Date signal: "
        f"{bool(detected_dates)}"
    )

    print(
        f"   Future date: "
        f"{future_date}"
    )

    print(
        f"   India location: "
        f"{has_india}"
    )

    print(
        f"   Online signal: "
        f"{has_online}"
    )

    print(
        f"   Registration: "
        f"{has_registration}"
    )

    return result


# ============================================================
# VERIFICATION SCORE
# ============================================================

def verification_score(
    result: VerificationResult,
) -> int:

    if not result.reachable:
        return 0

    score = 0

    # Cybersecurity relevance.
    if result.has_cyber_signal:
        score += 20

    # Event relevance.
    if result.has_event_signal:
        score += 15

    # Actual date exists.
    if result.has_date_signal:
        score += 10

    # Date is future.
    if result.has_future_date:
        score += 25

    # India location or online.
    if result.has_location_signal:
        score += 15

    # Registration.
    if result.has_registration_signal:
        score += 15

    return min(
        score,
        100,
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_url = (
        "https://owasp.org/events/"
    )

    result = verify_event(
        test_url
    )

    score = verification_score(
        result
    )

    print()
    print("=" * 60)
    print(
        f"VERIFICATION SCORE: "
        f"{score}/100"
    )
    print("=" * 60)
