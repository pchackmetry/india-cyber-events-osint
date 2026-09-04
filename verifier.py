from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

TIMEOUT = 20
INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")


# ============================================================
# VERIFICATION RESULT
# ============================================================

@dataclass
class VerificationResult:
    reachable: bool = False

    title: str = ""
    text: str = ""

    # Verification signals
    has_registration_signal: bool = False
    has_date_signal: bool = False
    has_future_date: bool = False
    has_location_signal: bool = False
    has_india_location: bool = False
    has_online_signal: bool = False
    has_cyber_signal: bool = False
    has_event_signal: bool = False

    # Date information
    detected_dates: list[str] = field(default_factory=list)
    event_date: str = ""
    event_end_date: str = ""

    # Rich event information
    event_time: str = ""
    event_location: str = ""
    event_venue: str = ""
    event_city: str = ""
    event_state: str = ""
    event_country: str = ""
    event_mode: str = ""
    event_organizer: str = ""
    event_type: str = ""
    event_price: str = ""

    # URLs
    registration_url: str = ""
    event_url: str = ""

    # Description
    event_description: str = ""


# ============================================================
# KEYWORDS
# ============================================================

CYBER_KEYWORDS = (
    "cybersecurity",
    "cyber security",
    "information security",
    "infosec",
    "application security",
    "appsec",
    "network security",
    "cloud security",
    "security operations",
    "soc",
    "penetration testing",
    "penetration test",
    "ethical hacking",
    "ethical hacker",
    "vulnerability",
    "vulnerabilities",
    "vapt",
    "bug bounty",
    "threat intelligence",
    "incident response",
    "digital forensics",
    "forensics",
    "malware",
    "ransomware",
    "zero trust",
    "identity security",
    "iam",
    "devsecops",
    "secure coding",
    "data security",
    "privacy",
    "grc",
    "risk management",
    "compliance",
    "security conference",
)


EVENT_KEYWORDS = (
    "conference",
    "summit",
    "webinar",
    "workshop",
    "meetup",
    "training",
    "bootcamp",
    "hackathon",
    "seminar",
    "symposium",
    "event",
    "forum",
    "expo",
    "competition",
    "challenge",
)


INDIA_KEYWORDS = (
    "india",
    "indian",
    "hyderabad",
    "bangalore",
    "bengaluru",
    "chennai",
    "mumbai",
    "pune",
    "delhi",
    "new delhi",
    "gurgaon",
    "gurugram",
    "noida",
    "kolkata",
    "ahmedabad",
    "jaipur",
    "kochi",
    "coimbatore",
    "thiruvananthapuram",
    "telangana",
    "karnataka",
    "tamil nadu",
    "maharashtra",
    "kerala",
    "gujarat",
    "rajasthan",
    "uttar pradesh",
    "virtual",
    "online",
)


LOCATION_KEYWORDS = (
    "hyderabad",
    "bangalore",
    "bengaluru",
    "chennai",
    "mumbai",
    "pune",
    "delhi",
    "new delhi",
    "gurgaon",
    "gurugram",
    "noida",
    "kolkata",
    "ahmedabad",
    "jaipur",
    "kochi",
    "india",
    "telangana",
    "karnataka",
    "tamil nadu",
    "maharashtra",
    "kerala",
    "virtual",
    "online",
    "remote",
)


# ============================================================
# DATE PARSING
# ============================================================

DATE_PATTERNS = (
    # 21 September 2026
    r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{4}\b",

    # September 21, 2026
    r"\b(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},\s+\d{4}\b",

    # 21 Sep 2026
    r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"\s+\d{4}\b",

    # Sep 21, 2026
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"\s+\d{1,2},\s+\d{4}\b",

    # 21/09/2026
    r"\b\d{1,2}/\d{1,2}/\d{4}\b",

    # 21-09-2026
    r"\b\d{1,2}-\d{1,2}-\d{4}\b",

    # 2026-09-21
    r"\b\d{4}-\d{1,2}-\d{1,2}\b",
)


def parse_date(value: str) -> date | None:
    """Parse a supported date string."""

    value = value.strip()

    formats = (
        "%d %B %Y",
        "%B %d, %Y",
        "%B %d %Y",
        "%d %b %Y",
        "%b %d, %Y",
        "%b %d %Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def _expand_date_range(match: str) -> list[str]:
    """
    Convert common date ranges into individual date strings.

    Examples:
        4-5 September 2026
        September 4-5, 2026
    """

    results = []

    # 4-5 September 2026
    pattern1 = re.search(
        r"\b(\d{1,2})\s*[-–]\s*(\d{1,2})\s+"
        r"(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+(\d{4})\b",
        match,
        re.IGNORECASE,
    )

    if pattern1:
        start_day = int(pattern1.group(1))
        end_day = int(pattern1.group(2))
        month = pattern1.group(3)
        year = int(pattern1.group(4))

        for day_number in range(start_day, end_day + 1):
            results.append(
                f"{day_number} {month} {year}"
            )

        return results

    # September 4-5, 2026
    pattern2 = re.search(
        r"\b(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+"
        r"(\d{1,2})\s*[-–]\s*(\d{1,2}),\s*(\d{4})\b",
        match,
        re.IGNORECASE,
    )

    if pattern2:
        month = pattern2.group(1)
        start_day = int(pattern2.group(2))
        end_day = int(pattern2.group(3))
        year = int(pattern2.group(4))

        for day_number in range(start_day, end_day + 1):
            results.append(
                f"{month} {day_number}, {year}"
            )

        return results

    return [match]


def extract_dates(text: str) -> list[str]:
    """Extract unique event dates from page text."""

    found = []

    # Search ranges first
    range_patterns = (
        r"\b\d{1,2}\s*[-–]\s*\d{1,2}\s+"
        r"(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{4}\b",

        r"\b(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+"
        r"\d{1,2}\s*[-–]\s*\d{1,2},\s*\d{4}\b",
    )

    for pattern in range_patterns:
        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        for match in matches:
            found.extend(
                _expand_date_range(match)
            )

    # Search individual dates
    for pattern in DATE_PATTERNS:
        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        for match in matches:
            if isinstance(match, tuple):
                continue

            found.append(match)

    # Remove invalid dates and duplicates
    result = []

    for value in found:
        if parse_date(value) is None:
            continue

        if value not in result:
            result.append(value)

    return result


# ============================================================
# TODAY FILTER
# ============================================================

def event_is_today(detected_dates: list[str]) -> bool:
    """
    Return True when the event is happening today in India.

    Examples:

    Today:
        True

    Tomorrow:
        False

    Yesterday:
        False

    Multi-day event containing today:
        True

    Unknown date:
        False
    """

    today = datetime.now(
        INDIA_TIMEZONE
    ).date()

    parsed_dates = []

    for value in detected_dates:

        parsed = parse_date(value)

        if parsed:
            parsed_dates.append(parsed)

    if not parsed_dates:
        return False

    if today in parsed_dates:
        return True

    earliest = min(parsed_dates)
    latest = max(parsed_dates)

    return earliest <= today <= latest


# ============================================================
# TEXT SIGNALS
# ============================================================

def contains_keyword(
    text: str,
    keywords: tuple[str, ...],
) -> bool:

    lowered = text.lower()

    return any(
        keyword.lower() in lowered
        for keyword in keywords
    )


def detect_event_type(text: str) -> str:

    lowered = text.lower()

    mapping = (
        ("conference", "Conference"),
        ("summit", "Summit"),
        ("webinar", "Webinar"),
        ("workshop", "Workshop"),
        ("meetup", "Meetup"),
        ("hackathon", "Hackathon"),
        ("bootcamp", "Bootcamp"),
        ("training", "Training"),
        ("seminar", "Seminar"),
        ("symposium", "Symposium"),
        ("expo", "Expo"),
        ("forum", "Forum"),
        ("competition", "Competition"),
        ("challenge", "Challenge"),
    )

    for keyword, label in mapping:

        if keyword in lowered:
            return label

    return ""


def detect_event_mode(text: str) -> str:

    lowered = text.lower()

    online = any(
        value in lowered
        for value in (
            "online",
            "virtual",
            "remote",
            "zoom",
            "webex",
            "microsoft teams",
            "google meet",
        )
    )

    offline = any(
        value in lowered
        for value in (
            "in person",
            "in-person",
            "onsite",
            "on-site",
            "venue",
            "hall",
            "hotel",
            "convention centre",
            "convention center",
        )
    )

    if online and offline:
        return "Hybrid"

    if online:
        return "Online"

    if offline:
        return "Offline"

    return ""


# ============================================================
# LOCATION EXTRACTION
# ============================================================

def clean_value(value: str) -> str:

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip(
        " \t\r\n:|-–—"
    )


def extract_location(text: str) -> str:

    patterns = (
        r"(?:location|venue|where)\s*[:\-]\s*"
        r"([^\n|]{3,150})",

        r"(?:held at|hosted at|located at)\s+"
        r"([^\n|]{3,150})",
    )

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:

            value = clean_value(
                match.group(1)
            )

            if value:
                return value

    # Try well-known Indian cities
    cities = (
        "Hyderabad",
        "Bangalore",
        "Bengaluru",
        "Chennai",
        "Mumbai",
        "Pune",
        "New Delhi",
        "Delhi",
        "Gurgaon",
        "Gurugram",
        "Noida",
        "Kolkata",
        "Ahmedabad",
        "Jaipur",
        "Kochi",
    )

    for city in cities:

        if re.search(
            rf"\b{re.escape(city)}\b",
            text,
            flags=re.IGNORECASE,
        ):

            return city

    # Online event
    if re.search(
        r"\b(virtual|online|remote)\b",
        text,
        flags=re.IGNORECASE,
    ):
        return "Online / Virtual"

    return ""


def extract_venue(text: str) -> str:

    patterns = (
        r"(?:venue)\s*[:\-]\s*([^\n|]{3,150})",

        r"(?:venue name)\s*[:\-]\s*([^\n|]{3,150})",

        r"(?:at|@)\s+"
        r"([A-Z][A-Za-z0-9&' .,\-]{3,100})",
    )

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:

            value = clean_value(
                match.group(1)
            )

            if value:
                return value

    return ""


# ============================================================
# ORGANIZER EXTRACTION
# ============================================================

def extract_organizer(text: str) -> str:

    patterns = (
        r"(?:organizer|organiser)\s*[:\-]\s*"
        r"([^\n|]{3,150})",

        r"(?:organized by|organised by)\s+"
        r"([^\n|]{3,150})",

        r"(?:hosted by)\s+"
        r"([^\n|]{3,150})",
    )

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:

            value = clean_value(
                match.group(1)
            )

            if value:
                return value

    return ""


# ============================================================
# TIME EXTRACTION
# ============================================================

def extract_time(text: str) -> str:

    patterns = (
        # 10:00 AM - 5:00 PM
        r"\b\d{1,2}:\d{2}\s*(?:AM|PM)"
        r"\s*[-–—]\s*"
        r"\d{1,2}:\d{2}\s*(?:AM|PM)\b",

        # 10 AM - 5 PM
        r"\b\d{1,2}\s*(?:AM|PM)"
        r"\s*[-–—]\s*"
        r"\d{1,2}\s*(?:AM|PM)\b",

        # 10:00 AM
        r"\b\d{1,2}:\d{2}\s*(?:AM|PM)\b",

        # 10 AM
        r"\b\d{1,2}\s*(?:AM|PM)\b",
    )

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return clean_value(
                match.group(0)
            )

    return ""


# ============================================================
# PRICE EXTRACTION
# ============================================================

def extract_price(text: str) -> str:

    patterns = (
        r"(?:price|fee|fees|registration fee|ticket)"
        r"\s*[:\-]\s*"
        r"((?:₹|Rs\.?|INR|\$)\s*[\d,]+"
        r"(?:\.\d{1,2})?)",

        r"\bfree\s+(?:registration|entry|event)\b",

        r"\bfree\b",
    )

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:

            value = clean_value(
                match.group(0)
            )

            if value:
                return value

    return ""


# ============================================================
# REGISTRATION URL
# ============================================================

def extract_registration_url(
    soup: BeautifulSoup,
    base_url: str,
) -> str:

    for link in soup.find_all(
        "a",
        href=True,
    ):

        label = link.get_text(
            " ",
            strip=True,
        ).lower()

        href = link.get(
            "href",
            "",
        ).strip()

        if not href:
            continue

        if any(
            keyword in label
            for keyword in (
                "register",
                "registration",
                "tickets",
                "ticket",
                "sign up",
                "signup",
                "book now",
                "join",
            )
        ):

            return requests.compat.urljoin(
                base_url,
                href,
            )

    return ""


# ============================================================
# DESCRIPTION
# ============================================================

def extract_description(
    soup: BeautifulSoup,
) -> str:

    # Meta description first
    meta = soup.find(
        "meta",
        attrs={
            "name": "description"
        },
    )

    if meta:

        content = meta.get(
            "content",
            "",
        ).strip()

        if len(content) >= 30:
            return content[:600]

    # OpenGraph description
    og = soup.find(
        "meta",
        attrs={
            "property": "og:description"
        },
    )

    if og:

        content = og.get(
            "content",
            "",
        ).strip()

        if len(content) >= 30:
            return content[:600]

    # First meaningful paragraph
    for paragraph in soup.find_all("p"):

        text = paragraph.get_text(
            " ",
            strip=True,
        )

        if len(text) >= 50:

            return text[:600]

    return ""


# ============================================================
# EVENT DATE DISPLAY
# ============================================================

def format_event_dates(
    detected_dates: list[str],
) -> tuple[str, str]:

    parsed = []

    for value in detected_dates:

        parsed_date = parse_date(value)

        if parsed_date:
            parsed.append(
                parsed_date
            )

    if not parsed:
        return "", ""

    parsed = sorted(
        set(parsed)
    )

    start = parsed[0]

    end = parsed[-1]

    start_display = start.strftime(
        "%d %B %Y"
    )

    end_display = end.strftime(
        "%d %B %Y"
    )

    if start == end:
        return start_display, ""

    return start_display, end_display


# ============================================================
# MAIN VERIFICATION
# ============================================================

def verify_event(
    url: str,
) -> VerificationResult:

    result = VerificationResult(
        event_url=url
    )

    try:

        response = requests.get(
            url,
            timeout=TIMEOUT,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/120 Safari/537.36"
                )
            },
            allow_redirects=True,
        )

        response.raise_for_status()

        result.reachable = True

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        # Remove unnecessary elements
        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "svg",
            ]
        ):
            tag.decompose()

        title = ""

        if soup.title:

            title = soup.title.get_text(
                " ",
                strip=True,
            )

        result.title = clean_value(
            title
        )

        text = soup.get_text(
            "\n",
            strip=True,
        )

        result.text = text

        combined_text = (
            f"{result.title}\n{text}"
        )

        lowered = combined_text.lower()

        # ----------------------------------------------------
        # Signals
        # ----------------------------------------------------

        result.has_cyber_signal = (
            contains_keyword(
                combined_text,
                CYBER_KEYWORDS,
            )
        )

        result.has_event_signal = (
            contains_keyword(
                combined_text,
                EVENT_KEYWORDS,
            )
        )

        result.has_location_signal = (
            contains_keyword(
                combined_text,
                LOCATION_KEYWORDS,
            )
        )

        result.has_india_location = (
            contains_keyword(
                combined_text,
                INDIA_KEYWORDS,
            )
        )

        result.has_online_signal = (
            detect_event_mode(
                combined_text
            ) in (
                "Online",
                "Hybrid",
            )
        )

        result.has_registration_signal = (
            any(
                keyword in lowered
                for keyword in (
                    "register",
                    "registration",
                    "tickets",
                    "ticket",
                    "sign up",
                    "signup",
                )
            )
        )

        # ----------------------------------------------------
        # Dates
        # ----------------------------------------------------

        result.detected_dates = (
            extract_dates(
                combined_text
            )
        )

        result.has_date_signal = bool(
            result.detected_dates
        )

        result.has_future_date = (
            any(
                (
                    parsed := parse_date(value)
                )
                and parsed
                >= datetime.now(
                    INDIA_TIMEZONE
                ).date()
                for value in result.detected_dates
            )
        )

        (
            result.event_date,
            result.event_end_date,
        ) = format_event_dates(
            result.detected_dates
        )

        # ----------------------------------------------------
        # Rich event fields
        # ----------------------------------------------------

        result.event_time = (
            extract_time(
                combined_text
            )
        )

        result.event_location = (
            extract_location(
                combined_text
            )
        )

        result.event_venue = (
            extract_venue(
                combined_text
            )
        )

        result.event_organizer = (
            extract_organizer(
                combined_text
            )
        )

        result.event_type = (
            detect_event_type(
                combined_text
            )
        )

        result.event_mode = (
            detect_event_mode(
                combined_text
            )
        )

        result.event_price = (
            extract_price(
                combined_text
            )
        )

        result.registration_url = (
            extract_registration_url(
                soup,
                response.url,
            )
        )

        result.event_description = (
            extract_description(
                soup
            )
        )

        # ----------------------------------------------------
        # Try to identify city/state/country
        # ----------------------------------------------------

        city_state_pairs = (
            (
                "Hyderabad",
                "Telangana",
                "India",
            ),
            (
                "Bangalore",
                "Karnataka",
                "India",
            ),
            (
                "Bengaluru",
                "Karnataka",
                "India",
            ),
            (
                "Chennai",
                "Tamil Nadu",
                "India",
            ),
            (
                "Mumbai",
                "Maharashtra",
                "India",
            ),
            (
                "Pune",
                "Maharashtra",
                "India",
            ),
            (
                "New Delhi",
                "Delhi",
                "India",
            ),
            (
                "Delhi",
                "Delhi",
                "India",
            ),
            (
                "Kolkata",
                "West Bengal",
                "India",
            ),
            (
                "Ahmedabad",
                "Gujarat",
                "India",
            ),
            (
                "Jaipur",
                "Rajasthan",
                "India",
            ),
            (
                "Kochi",
                "Kerala",
                "India",
            ),
        )

        for city, state, country in city_state_pairs:

            if re.search(
                rf"\b{re.escape(city)}\b",
                combined_text,
                flags=re.IGNORECASE,
            ):

                result.event_city = city
                result.event_state = state
                result.event_country = country

                break

        # India country
        if (
            not result.event_country
            and re.search(
                r"\bindia\b",
                combined_text,
                flags=re.IGNORECASE,
            )
        ):
            result.event_country = "India"

        # Online location fallback
        if (
            not result.event_location
            and result.event_mode == "Online"
        ):
            result.event_location = (
                "Online / Virtual"
            )

        # If location is simply city
        if (
            result.event_location
            and not result.event_city
        ):
            for city, state, country in city_state_pairs:

                if re.search(
                    rf"\b{re.escape(city)}\b",
                    result.event_location,
                    flags=re.IGNORECASE,
                ):

                    result.event_city = city
                    result.event_state = state
                    result.event_country = country

                    break

        return result

    except (
        requests.RequestException,
        ValueError,
        UnicodeError,
    ):

        result.reachable = False

        return result


# ============================================================
# VERIFICATION SCORE
# ============================================================

def verification_score(
    result: VerificationResult,
) -> int:

    score = 0

    if result.has_cyber_signal:
        score += 20

    if result.has_event_signal:
        score += 15

    if result.has_date_signal:
        score += 10

    if result.has_future_date:
        score += 25

    if result.has_location_signal:
        score += 15

    if result.has_registration_signal:
        score += 15

    return min(
        score,
        100,
    )
