from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


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

INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")


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
    """Fetch webpage HTML."""

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
    """Extract title and visible text."""

    soup = BeautifulSoup(
        html,
        "lxml",
    )

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
    """Check whether any keyword exists in text."""

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
    """
    Extract common event date formats.

    Supported examples:

    4 September 2026
    04 September 2026
    4 Sep 2026
    September 4, 2026
    Sep 4, 2026
    04/09/2026
    04-09-2026
    2026-09-04

    Multi-day examples:

    4-5 September 2026
    September 4-5, 2026
    """

    matches: list[str] = []

    # --------------------------------------------------------
    # Multi-day: 4-5 September 2026
    # --------------------------------------------------------

    pattern = re.compile(
        r"\b"
        r"(\d{1,2})"
        r"\s*-\s*"
        r"(\d{1,2})"
        r"\s+"
        r"(January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+"
        r"(\d{4})"
        r"\b",
        re.IGNORECASE,
    )

    for match in pattern.finditer(text):
        start_day = match.group(1)
        end_day = match.group(2)
        month = match.group(3)
        year = match.group(4)

        matches.append(
            f"{start_day} {month} {year}"
        )

        matches.append(
            f"{end_day} {month} {year}"
        )

    # --------------------------------------------------------
    # Multi-day: September 4-5, 2026
    # --------------------------------------------------------

    pattern = re.compile(
        r"\b"
        r"(January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+"
        r"(\d{1,2})"
        r"\s*-\s*"
        r"(\d{1,2})"
        r",\s*"
        r"(\d{4})"
        r"\b",
        re.IGNORECASE,
    )

    for match in pattern.finditer(text):
        month = match.group(1)
        start_day = match.group(2)
        end_day = match.group(3)
        year = match.group(4)

        matches.append(
            f"{start_day} {month} {year}"
        )

        matches.append(
            f"{end_day} {month} {year}"
        )

    # --------------------------------------------------------
    # Full month: 4 September 2026
    # --------------------------------------------------------

    pattern = re.compile(
        r"\b"
        r"\d{1,2}"
        r"\s+"
        r"(January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+"
        r"\d{4}"
        r"\b",
        re.IGNORECASE,
    )

    matches.extend(
        match.group(0)
        for match in pattern.finditer(text)
    )

    # --------------------------------------------------------
    # Full month: September 4, 2026
    # --------------------------------------------------------

    pattern = re.compile(
        r"\b"
        r"(January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+"
        r"\d{1,2}"
        r",\s*"
        r"\d{4}"
        r"\b",
        re.IGNORECASE,
    )

    matches.extend(
        match.group(0)
        for match in pattern.finditer(text)
    )

    # --------------------------------------------------------
    # Short month: 4 Sep 2026
    # --------------------------------------------------------

    pattern = re.compile(
        r"\b"
        r"\d{1,2}"
        r"\s+"
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        r"[a-z]*"
        r"\s+"
        r"\d{4}"
        r"\b",
        re.IGNORECASE,
    )

    matches.extend(
        match.group(0)
        for match in pattern.finditer(text)
    )

    # --------------------------------------------------------
    # Short month: Sep 4, 2026
    # --------------------------------------------------------

    pattern = re.compile(
        r"\b"
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        r"[a-z]*"
        r"\s+"
        r"\d{1,2}"
        r",?\s+"
        r"\d{4}"
        r"\b",
        re.IGNORECASE,
    )

    matches.extend(
        match.group(0)
        for match in pattern.finditer(text)
    )

    # --------------------------------------------------------
    # Numeric: 04/09/2026 or 04-09-2026
    # --------------------------------------------------------

    pattern = re.compile(
        r"\b"
        r"\d{1,2}"
        r"[/-]"
        r"\d{1,2}"
        r"[/-]"
        r"\d{4}"
        r"\b"
    )

    matches.extend(
        match.group(0)
        for match in pattern.finditer(text)
    )

    # --------------------------------------------------------
    # ISO: 2026-09-04
    # --------------------------------------------------------

    pattern = re.compile(
        r"\b"
        r"\d{4}-\d{2}-\d{2}"
        r"\b"
    )

    matches.extend(
        match.group(0)
        for match in pattern.finditer(text)
    )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    unique_dates: list[str] = []

    for value in matches:
        value = value.strip()

        if value and value not in unique_dates:
            unique_dates.append(value)

    return unique_dates


# ============================================================
# PARSE DATE
# ============================================================

def parse_date(
    date_text: str,
) -> date | None:
    """Convert detected date text into a date object."""

    cleaned = date_text.strip()

    formats = [
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %d %Y",
        "%b %d %Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                cleaned,
                fmt,
            ).date()

        except ValueError:
            continue

    return None


# ============================================================
# GET INDIA TODAY
# ============================================================

def get_india_today() -> date:
    """Return today's date using India timezone."""

    return datetime.now(
        INDIA_TIMEZONE
    ).date()


# ============================================================
# EVENT IS TODAY
# ============================================================

def event_is_today(
    detected_dates: list[str],
) -> bool:
    """
    Return True if at least one detected event date
    is today in India.
    """

    today = get_india_today()

    for date_text in detected_dates:
        parsed = parse_date(date_text)

        if parsed == today:
            return True

    return False


# ============================================================
# EVENT IS FUTURE
# ============================================================

def has_future_date(
    detected_dates: list[str],
) -> bool:
    """
    Return True if the event has a date today or later.

    This is retained for compatibility with the existing
    verification scoring system.
    """

    today = get_india_today()

    for date_text in detected_dates:
        parsed = parse_date(date_text)

        if parsed is not None and parsed >= today:
            return True

    return False


# ============================================================
# LOCATION CHECK
# ============================================================

def location_signals(
    text: str,
) -> tuple[bool, bool, bool]:
    """Detect India and online location signals."""

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
    """Detect event registration signals."""

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
    """Fetch and verify an event webpage."""

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

    today_event = event_is_today(
        detected_dates
    )

    has_location, has_india, has_online = (
        location_signals(text)
    )

    has_registration = registration_signal(
        soup,
        text,
    )

    combined_text = (
        f"{title} {text}"
    )

    has_cyber = contains_keyword(
        combined_text,
        CYBER_KEYWORDS,
    )

    has_event = contains_keyword(
        combined_text,
        EVENT_KEYWORDS,
    )

    result = VerificationResult(
        reachable=True,
        title=title,
        text=text,
        has_registration_signal=has_registration,
        has_date_signal=bool(detected_dates),
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
        f"   Detected dates: "
        f"{detected_dates}"
    )

    print(
        f"   India today: "
        f"{get_india_today()}"
    )

    print(
        f"   Event TODAY: "
        f"{today_event}"
    )

    print(
        f"   Future/today date: "
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
    """Calculate event verification score."""

    if not result.reachable:
        return 0

    score = 0

    # Cybersecurity relevance
    if result.has_cyber_signal:
        score += 20

    # Event relevance
    if result.has_event_signal:
        score += 15

    # Date exists
    if result.has_date_signal:
        score += 10

    # Today or future
    if result.has_future_date:
        score += 25

    # India or online
    if result.has_location_signal:
        score += 15

    # Registration
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

    print("=" * 60)
    print("🇮🇳 VERIFIER TEST")
    print("=" * 60)

    print(
        f"India date: "
        f"{get_india_today()}"
    )

    print()

    test_dates = [
        "4 September 2026",
        "5 September 2026",
        "04/09/2026",
        "2026-09-04",
        "4 Sep 2026",
        "September 4, 2026",
    ]

    for test_date in test_dates:

        parsed = parse_date(
            test_date
        )

        today = (
            parsed == get_india_today()
            if parsed
            else False
        )

        print(
            f"{test_date:25} "
            f"→ {parsed} "
            f"→ TODAY={today}"
        )

    print()
    print("=" * 60)

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
