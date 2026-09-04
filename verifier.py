from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo


# ============================================================
# CONFIGURATION
# ============================================================

TIMEOUT = 20
INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)


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

    # New accuracy metadata
    date_source: str = ""
    location_source: str = ""
    structured_event_found: bool = False


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
    "telangana",
    "karnataka",
    "tamil nadu",
    "maharashtra",
    "kerala",
    "gujarat",
    "rajasthan",
    "uttar pradesh",
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

CITY_STATE_COUNTRY = (
    ("Hyderabad", "Telangana", "India"),
    ("Bangalore", "Karnataka", "India"),
    ("Bengaluru", "Karnataka", "India"),
    ("Chennai", "Tamil Nadu", "India"),
    ("Mumbai", "Maharashtra", "India"),
    ("Pune", "Maharashtra", "India"),
    ("New Delhi", "Delhi", "India"),
    ("Delhi", "Delhi", "India"),
    ("Gurgaon", "Haryana", "India"),
    ("Gurugram", "Haryana", "India"),
    ("Noida", "Uttar Pradesh", "India"),
    ("Kolkata", "West Bengal", "India"),
    ("Ahmedabad", "Gujarat", "India"),
    ("Jaipur", "Rajasthan", "India"),
    ("Kochi", "Kerala", "India"),
    ("Coimbatore", "Tamil Nadu", "India"),
)


# ============================================================
# HELPERS
# ============================================================

def clean_value(value: object) -> str:
    if value is None:
        return ""

    value = str(value)

    value = re.sub(r"\s+", " ", value)

    return value.strip(" \t\r\n:|-–—")


def contains_keyword(
    text: str,
    keywords: tuple[str, ...],
) -> bool:
    lowered = text.lower()

    return any(
        keyword.lower() in lowered
        for keyword in keywords
    )


def today_india() -> date:
    return datetime.now(INDIA_TIMEZONE).date()


def safe_text(value: object) -> str:
    return clean_value(value)


# ============================================================
# DATE PARSING
# ============================================================

MONTHS = (
    "January|February|March|April|May|June|July|August|"
    "September|October|November|December"
)

SHORT_MONTHS = (
    "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
)


DATE_PATTERNS = (
    rf"\b\d{{1,2}}\s+(?:{MONTHS})\s+\d{{4}}\b",
    rf"\b(?:{MONTHS})\s+\d{{1,2}},\s+\d{{4}}\b",
    rf"\b\d{{1,2}}\s+(?:{SHORT_MONTHS})\s+\d{{4}}\b",
    rf"\b(?:{SHORT_MONTHS})\s+\d{{1,2}},\s+\d{{4}}\b",
    r"\b\d{1,2}/\d{1,2}/\d{4}\b",
    r"\b\d{1,2}-\d{1,2}-\d{4}\b",
    r"\b\d{4}-\d{1,2}-\d{1,2}\b",
)


def parse_date(value: str) -> date | None:
    value = clean_value(value)

    formats = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d %B %Y",
        "%B %d, %Y",
        "%B %d %Y",
        "%d %b %Y",
        "%b %d, %Y",
        "%b %d %Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%m-%d-%Y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    return None


def iso_to_date(value: object) -> date | None:
    if not value:
        return None

    text = str(value).strip()

    # ISO date/datetime
    try:
        return datetime.fromisoformat(
            text.replace("Z", "+00:00")
        ).date()
    except ValueError:
        pass

    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        pass

    return parse_date(text)


def expand_date_range(value: str) -> list[date]:
    value = clean_value(value)

    results: list[date] = []

    # 4-5 September 2026
    match = re.search(
        rf"\b(\d{{1,2}})\s*[-–]\s*(\d{{1,2}})\s+"
        rf"({MONTHS})\s+(\d{{4}})\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        start_day = int(match.group(1))
        end_day = int(match.group(2))
        month = match.group(3)
        year = int(match.group(4))

        for day_number in range(start_day, end_day + 1):
            parsed = parse_date(
                f"{day_number} {month} {year}"
            )

            if parsed:
                results.append(parsed)

        return results

    # September 4-5, 2026
    match = re.search(
        rf"\b({MONTHS})\s+"
        rf"(\d{{1,2}})\s*[-–]\s*(\d{{1,2}}),\s*(\d{{4}})\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        month = match.group(1)
        start_day = int(match.group(2))
        end_day = int(match.group(3))
        year = int(match.group(4))

        for day_number in range(start_day, end_day + 1):
            parsed = parse_date(
                f"{month} {day_number}, {year}"
            )

            if parsed:
                results.append(parsed)

        return results

    parsed = parse_date(value)

    if parsed:
        return [parsed]

    return []


def dates_to_strings(values: list[date]) -> list[str]:
    unique = sorted(set(values))

    return [
        value.strftime("%d %B %Y")
        for value in unique
    ]


def format_event_dates(
    detected_dates: list[str],
) -> tuple[str, str]:

    parsed: list[date] = []

    for value in detected_dates:
        parsed.extend(
            expand_date_range(value)
        )

    parsed = sorted(set(parsed))

    if not parsed:
        return "", ""

    start = parsed[0]
    end = parsed[-1]

    start_display = start.strftime(
        "%d %B %Y"
    )

    if start == end:
        return start_display, ""

    return (
        start_display,
        end.strftime("%d %B %Y"),
    )


def event_is_today(
    detected_dates: list[str],
) -> bool:

    if not detected_dates:
        return False

    today = today_india()

    parsed: list[date] = []

    for value in detected_dates:
        parsed.extend(
            expand_date_range(value)
        )

    parsed = sorted(set(parsed))

    if not parsed:
        return False

    return min(parsed) <= today <= max(parsed)


# ============================================================
# JSON-LD / STRUCTURED EVENT DATA
# ============================================================

def iter_json_objects(value: object):
    if isinstance(value, dict):
        yield value

        for child in value.values():
            yield from iter_json_objects(child)

    elif isinstance(value, list):
        for child in value:
            yield from iter_json_objects(child)


def is_event_type(value: object) -> bool:
    if isinstance(value, str):
        return value.lower().endswith("event")

    if isinstance(value, list):
        return any(
            is_event_type(item)
            for item in value
        )

    return False


def extract_jsonld_events(
    soup: BeautifulSoup,
) -> list[dict]:

    events: list[dict] = []

    for script in soup.find_all(
        "script",
        attrs={"type": re.compile(
            r"application/ld\+json",
            re.IGNORECASE,
        )},
    ):
        raw = script.string or script.get_text()

        if not raw:
            continue

        raw = raw.strip()

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue

        for obj in iter_json_objects(data):
            if not isinstance(obj, dict):
                continue

            if is_event_type(obj.get("@type")):
                events.append(obj)

    return events


def jsonld_address(
    location: object,
) -> str:

    if isinstance(location, str):
        return clean_value(location)

    if not isinstance(location, dict):
        return ""

    address = location.get("address")

    if isinstance(address, str):
        return clean_value(address)

    if isinstance(address, dict):
        parts = []

        for key in (
            "streetAddress",
            "addressLocality",
            "addressRegion",
            "postalCode",
            "addressCountry",
        ):
            value = address.get(key)

            if value:
                parts.append(
                    clean_value(value)
                )

        return ", ".join(parts)

    parts = []

    for key in (
        "name",
        "streetAddress",
        "addressLocality",
        "addressRegion",
        "addressCountry",
    ):
        value = location.get(key)

        if value:
            parts.append(
                clean_value(value)
            )

    return ", ".join(parts)


def extract_structured_event(
    events: list[dict],
) -> dict:

    if not events:
        return {}

    today = today_india()

    scored: list[tuple[int, dict]] = []

    for event in events:

        score = 0

        start = iso_to_date(
            event.get("startDate")
        )

        end = iso_to_date(
            event.get("endDate")
        ) or start

        if start:
            score += 40

            if end and start <= today <= end:
                score += 100

            elif start >= today:
                score += 50

        if event.get("location"):
            score += 20

        if event.get("name"):
            score += 15

        if event.get("organizer"):
            score += 10

        if event.get("eventStatus"):
            score += 5

        scored.append(
            (score, event)
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return scored[0][1]


# ============================================================
# FOCUSED DATE EXTRACTION
# ============================================================

def extract_dates_from_text(
    text: str,
) -> list[str]:

    found: list[str] = []

    # Ranges first
    range_patterns = (
        rf"\b\d{{1,2}}\s*[-–]\s*\d{{1,2}}\s+"
        rf"(?:{MONTHS})\s+\d{{4}}\b",

        rf"\b(?:{MONTHS})\s+"
        rf"\d{{1,2}}\s*[-–]\s*\d{{1,2}},\s*\d{{4}}\b",
    )

    for pattern in range_patterns:
        for match in re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            found.append(match)

    for pattern in DATE_PATTERNS:
        for match in re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            if match not in found:
                found.append(match)

    return found


def extract_focused_event_dates(
    soup: BeautifulSoup,
    title: str,
) -> tuple[list[str], str]:

    # --------------------------------------------------------
    # 1. Elements explicitly describing the event date
    # --------------------------------------------------------

    selectors = (
        "[datetime]",
        "time",
        ".date",
        ".event-date",
        ".event_date",
        ".eventDate",
        ".start-date",
        ".startDate",
        ".event-details",
        ".event-details__date",
        ".event-info",
        ".event-meta",
    )

    candidates: list[str] = []

    for selector in selectors:
        for element in soup.select(selector):

            value = (
                element.get("datetime")
                or element.get_text(
                    " ",
                    strip=True,
                )
            )

            if value:
                candidates.append(
                    clean_value(value)
                )

    # --------------------------------------------------------
    # 2. Heading/title vicinity
    # --------------------------------------------------------

    headings = soup.find_all(
        ["h1", "h2", "h3"]
    )

    for heading in headings[:10]:

        heading_text = heading.get_text(
            " ",
            strip=True,
        )

        if not heading_text:
            continue

        parent = heading.parent

        if parent:
            block = parent.get_text(
                " ",
                strip=True,
            )

            if len(block) <= 1200:
                candidates.append(block)

    # --------------------------------------------------------
    # 3. Date-labelled text
    # --------------------------------------------------------

    labelled_patterns = (
        r"(?:event date|date|when|starts|start date|"
        r"event starts|date and time)\s*[:\-]\s*"
        r"([^|]{5,200})",
    )

    body_text = soup.get_text(
        "\n",
        strip=True,
    )

    for pattern in labelled_patterns:
        matches = re.findall(
            pattern,
            body_text,
            flags=re.IGNORECASE,
        )

        candidates.extend(matches)

    # --------------------------------------------------------
    # Parse candidates
    # --------------------------------------------------------

    parsed: list[date] = []

    for candidate in candidates:

        for date_text in extract_dates_from_text(
            candidate
        ):

            parsed.extend(
                expand_date_range(date_text)
            )

        direct = iso_to_date(candidate)

        if direct:
            parsed.append(direct)

    parsed = sorted(set(parsed))

    # --------------------------------------------------------
    # Prefer today/future dates over old dates
    # --------------------------------------------------------

    today = today_india()

    relevant = [
        value
        for value in parsed
        if value >= today - timedelta(days=1)
    ]

    if relevant:
        parsed = relevant

    if not parsed:
        return [], ""

    # Avoid huge unrelated date ranges.
    # Event ranges normally span only a few days.
    if len(parsed) > 10:
        parsed = parsed[:10]

    return (
        dates_to_strings(parsed),
        "focused HTML/date extraction",
    )


# ============================================================
# LOCATION
# ============================================================

def structured_location(
    event: dict,
) -> tuple[str, str, str, str, str]:

    location = event.get("location")

    if not location:
        return "", "", "", "", ""

    if isinstance(location, str):
        return (
            clean_value(location),
            "",
            "",
            "",
            "JSON-LD",
        )

    if not isinstance(location, dict):
        return "", "", "", "", ""

    name = clean_value(
        location.get("name")
    )

    address = location.get("address")

    city = ""
    state = ""
    country = ""
    street = ""

    if isinstance(address, dict):

        street = clean_value(
            address.get("streetAddress")
        )

        city = clean_value(
            address.get("addressLocality")
        )

        state = clean_value(
            address.get("addressRegion")
        )

        country_value = address.get(
            "addressCountry"
        )

        if isinstance(
            country_value,
            dict,
        ):
            country = clean_value(
                country_value.get("name")
            )
        else:
            country = clean_value(
                country_value
            )

    elif isinstance(address, str):
        address = clean_value(address)

        for known_city, known_state, known_country in CITY_STATE_COUNTRY:
            if re.search(
                rf"\b{re.escape(known_city)}\b",
                address,
                flags=re.IGNORECASE,
            ):
                city = known_city
                state = known_state
                country = known_country
                break

    parts = [
        part
        for part in (
            street,
            city,
            state,
            country,
        )
        if part
    ]

    full = ", ".join(parts)

    if name and full:
        full = f"{name}, {full}"

    elif name:
        full = name

    return (
        full,
        name,
        city,
        state,
        country,
    )


def extract_location(
    text: str,
) -> str:

    patterns = (
        r"(?:location|where|venue address)"
        r"\s*[:\-]\s*([^\n|]{3,180})",

        r"(?:held at|hosted at|taking place at)"
        r"\s+([^\n|]{3,180})",
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

    for city, _, _ in CITY_STATE_COUNTRY:

        if re.search(
            rf"\b{re.escape(city)}\b",
            text,
            flags=re.IGNORECASE,
        ):
            return city

    if re.search(
        r"\b(virtual|online|remote)\b",
        text,
        flags=re.IGNORECASE,
    ):
        return "Online / Virtual"

    return ""


def extract_city_state_country(
    text: str,
) -> tuple[str, str, str]:

    for city, state, country in CITY_STATE_COUNTRY:

        if re.search(
            rf"\b{re.escape(city)}\b",
            text,
            flags=re.IGNORECASE,
        ):
            return city, state, country

    if re.search(
        r"\bindia\b",
        text,
        flags=re.IGNORECASE,
    ):
        return "", "", "India"

    return "", "", ""


# ============================================================
# VENUE
# ============================================================

def extract_venue(
    text: str,
) -> str:

    patterns = (
        r"(?:venue|venue name)"
        r"\s*[:\-]\s*([^\n|]{3,150})",

        r"(?:location)"
        r"\s*[:\-]\s*([^\n|]{3,150})",
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
# ORGANIZER
# ============================================================

def extract_organizer(
    text: str,
) -> str:

    patterns = (
        r"(?:organizer|organiser)"
        r"\s*[:\-]\s*([^\n|]{3,150})",

        r"(?:organized by|organised by)"
        r"\s+([^\n|]{3,150})",

        r"(?:hosted by)"
        r"\s+([^\n|]{3,150})",
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
# TIME
# ============================================================

def extract_time(
    text: str,
) -> str:

    patterns = (
        r"\b\d{1,2}:\d{2}\s*(?:AM|PM)"
        r"\s*[-–—]\s*"
        r"\d{1,2}:\d{2}\s*(?:AM|PM)\b",

        r"\b\d{1,2}\s*(?:AM|PM)"
        r"\s*[-–—]\s*"
        r"\d{1,2}\s*(?:AM|PM)\b",

        r"\b\d{1,2}:\d{2}\s*(?:AM|PM)\b",

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
# EVENT TYPE / MODE
# ============================================================

def detect_event_type(
    text: str,
) -> str:

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


def detect_event_mode(
    text: str,
) -> str:

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
# PRICE
# ============================================================

def extract_price(
    text: str,
) -> str:

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
            return clean_value(
                match.group(0)
            )

    return ""


# ============================================================
# REGISTRATION URL
# ============================================================

def extract_registration_url(
    soup: BeautifulSoup,
    base_url: str,
) -> str:

    keywords = (
        "register",
        "registration",
        "tickets",
        "ticket",
        "sign up",
        "signup",
        "book now",
        "reserve",
        "join",
    )

    candidates = []

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
            for keyword in keywords
        ):
            candidates.append(
                urljoin(
                    base_url,
                    href,
                )
            )

    if candidates:
        return candidates[0]

    return ""


# ============================================================
# DESCRIPTION
# ============================================================

def extract_description(
    soup: BeautifulSoup,
) -> str:

    for attrs in (
        {"name": "description"},
        {"property": "og:description"},
    ):

        meta = soup.find(
            "meta",
            attrs=attrs,
        )

        if meta:

            content = clean_value(
                meta.get(
                    "content",
                    "",
                )
            )

            if len(content) >= 30:
                return content[:600]

    for paragraph in soup.find_all("p"):

        text = paragraph.get_text(
            " ",
            strip=True,
        )

        if len(text) >= 50:
            return text[:600]

    return ""


# ============================================================
# STRUCTURED EVENT FIELDS
# ============================================================

def apply_structured_event(
    result: VerificationResult,
    event: dict,
    response_url: str,
) -> None:

    result.structured_event_found = True

    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    start = iso_to_date(
        event.get("startDate")
    )

    end = iso_to_date(
        event.get("endDate")
    ) or start

    if start:

        dates = [start]

        if end and end >= start:
            current = start

            while current <= end:
                dates.append(current)

                if len(dates) >= 15:
                    break

                current += timedelta(days=1)

        result.detected_dates = dates_to_strings(
            dates
        )

        result.event_date = start.strftime(
            "%d %B %Y"
        )

        if end and end != start:
            result.event_end_date = end.strftime(
                "%d %B %Y"
            )

        result.date_source = "JSON-LD Event"

    # --------------------------------------------------------
    # Time
    # --------------------------------------------------------

    if event.get("startDate"):

        start_text = str(
            event.get("startDate")
        )

        time_match = re.search(
            r"T(\d{2}:\d{2})(?::\d{2})?",
            start_text,
        )

        if time_match:
            result.event_time = (
                time_match.group(1)
            )

    # --------------------------------------------------------
    # Name
    # --------------------------------------------------------

    structured_name = clean_value(
        event.get("name")
    )

    if structured_name:
        result.title = structured_name

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    description = clean_value(
        event.get("description")
    )

    if description:
        result.event_description = description[:600]

    # --------------------------------------------------------
    # Organizer
    # --------------------------------------------------------

    organizer = event.get(
        "organizer"
    )

    if isinstance(organizer, dict):

        result.event_organizer = clean_value(
            organizer.get("name")
        )

    elif isinstance(organizer, str):

        result.event_organizer = clean_value(
            organizer
        )

    # --------------------------------------------------------
    # Location
    # --------------------------------------------------------

    (
        full_location,
        venue,
        city,
        state,
        country,
    ) = structured_location(
        event
    )

    if full_location:
        result.event_location = full_location
        result.location_source = "JSON-LD"

    if venue:
        result.event_venue = venue

    if city:
        result.event_city = city

    if state:
        result.event_state = state

    if country:
        result.event_country = country

    # --------------------------------------------------------
    # Event type
    # --------------------------------------------------------

    event_text = (
        f"{result.title} "
        f"{result.event_description}"
    )

    result.event_type = (
        detect_event_type(
            event_text
        )
    )

    # --------------------------------------------------------
    # Event mode
    # --------------------------------------------------------

    result.event_mode = (
        detect_event_mode(
            f"{full_location} "
            f"{result.event_description}"
        )
    )

    # --------------------------------------------------------
    # Registration URL
    # --------------------------------------------------------

    offers = event.get("offers")

    if isinstance(offers, dict):

        url = clean_value(
            offers.get("url")
        )

        if url:
            result.registration_url = (
                urljoin(
                    response_url,
                    url,
                )
            )

    elif isinstance(offers, list):

        for offer in offers:

            if not isinstance(
                offer,
                dict,
            ):
                continue

            url = clean_value(
                offer.get("url")
            )

            if url:
                result.registration_url = (
                    urljoin(
                        response_url,
                        url,
                    )
                )
                break

    # --------------------------------------------------------
    # Price
    # --------------------------------------------------------

    if isinstance(offers, dict):

        price = clean_value(
            offers.get("price")
        )

        currency = clean_value(
            offers.get("priceCurrency")
        )

        if price:
            result.event_price = (
                f"{currency} {price}".strip()
            )


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
                "User-Agent": USER_AGENT,
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8"
                ),
            },
            allow_redirects=True,
        )

        response.raise_for_status()

        result.reachable = True

        final_url = response.url

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        # ----------------------------------------------------
        # Extract structured data BEFORE removing scripts
        # ----------------------------------------------------

        jsonld_events = (
            extract_jsonld_events(
                soup
            )
        )

        structured_event = (
            extract_structured_event(
                jsonld_events
            )
        )

        # ----------------------------------------------------
        # Page title
        # ----------------------------------------------------

        if soup.title:

            result.title = clean_value(
                soup.title.get_text(
                    " ",
                    strip=True,
                )
            )

        # ----------------------------------------------------
        # Apply structured event data
        # ----------------------------------------------------

        if structured_event:

            apply_structured_event(
                result,
                structured_event,
                final_url,
            )

        # ----------------------------------------------------
        # Remove noisy elements
        # ----------------------------------------------------

        for tag in soup.find_all(
            [
                "script",
                "style",
                "noscript",
                "svg",
            ]
        ):
            tag.decompose()

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

        result.has_registration_signal = (
            bool(
                result.registration_url
            )
            or any(
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
        # Date fallback
        # ----------------------------------------------------

        if not result.detected_dates:

            (
                fallback_dates,
                source,
            ) = extract_focused_event_dates(
                soup,
                result.title,
            )

            result.detected_dates = (
                fallback_dates
            )

            result.date_source = source

            (
                result.event_date,
                result.event_end_date,
            ) = format_event_dates(
                result.detected_dates
            )

        result.has_date_signal = bool(
            result.detected_dates
        )

        # ----------------------------------------------------
        # Future date
        # ----------------------------------------------------

        today = today_india()

        parsed_dates = []

        for value in result.detected_dates:

            parsed_dates.extend(
                expand_date_range(value)
            )

        result.has_future_date = any(
            parsed >= today
            for parsed in parsed_dates
        )

        # ----------------------------------------------------
        # Rich fields fallback
        # ----------------------------------------------------

        if not result.event_time:
            result.event_time = (
                extract_time(
                    combined_text
                )
            )

        if not result.event_location:

            result.event_location = (
                extract_location(
                    combined_text
                )
            )

            if result.event_location:
                result.location_source = (
                    "HTML/text extraction"
                )

        if not result.event_venue:

            result.event_venue = (
                extract_venue(
                    combined_text
                )
            )

        if not result.event_organizer:

            result.event_organizer = (
                extract_organizer(
                    combined_text
                )
            )

        if not result.event_type:

            result.event_type = (
                detect_event_type(
                    combined_text
                )
            )

        if not result.event_mode:

            result.event_mode = (
                detect_event_mode(
                    combined_text
                )
            )

        if not result.event_price:

            result.event_price = (
                extract_price(
                    combined_text
                )
            )

        if not result.registration_url:

            result.registration_url = (
                extract_registration_url(
                    soup,
                    final_url,
                )
            )

        if not result.event_description:

            result.event_description = (
                extract_description(
                    soup
                )
            )

        # ----------------------------------------------------
        # City/state/country fallback
        # ----------------------------------------------------

        if not result.event_city:

            (
                city,
                state,
                country,
            ) = extract_city_state_country(
                result.event_location
                or combined_text
            )

            result.event_city = city
            result.event_state = state
            result.event_country = country

        # ----------------------------------------------------
        # Country fallback
        # ----------------------------------------------------

        if (
            not result.event_country
            and re.search(
                r"\bindia\b",
                combined_text,
                flags=re.IGNORECASE,
            )
        ):
            result.event_country = "India"

        # ----------------------------------------------------
        # Online fallback
        # ----------------------------------------------------

        if (
            not result.event_location
            and result.event_mode
            in ("Online", "Hybrid")
        ):
            result.event_location = (
                "Online / Virtual"
            )

        # ----------------------------------------------------
        # Structured event date safety
        # ----------------------------------------------------

        if result.structured_event_found:

            # JSON-LD is trusted over arbitrary
            # page dates.
            result.has_date_signal = bool(
                result.detected_dates
            )

        return result

    except (
        requests.RequestException,
        ValueError,
        UnicodeError,
        json.JSONDecodeError,
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

    if result.reachable:
        score += 5

    if result.has_cyber_signal:
        score += 20

    if result.has_event_signal:
        score += 15

    if result.has_date_signal:
        score += 10

    if result.has_future_date:
        score += 15

    if result.has_location_signal:
        score += 10

    if result.has_registration_signal:
        score += 10

    if result.structured_event_found:
        score += 10

    if result.event_city or result.event_country:
        score += 5

    return min(
        score,
        100,
    )


# ============================================================
# OPTIONAL LOCAL TEST
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            "python verifier.py https://example.com/event"
        )

        raise SystemExit(1)

    test_url = sys.argv[1]

    result = verify_event(
        test_url
    )

    print()
    print("=" * 60)
    print("VERIFICATION RESULT")
    print("=" * 60)

    print(
        "Reachable:",
        result.reachable,
    )

    print(
        "Title:",
        result.title,
    )

    print(
        "Date:",
        result.event_date,
    )

    print(
        "End Date:",
        result.event_end_date,
    )

    print(
        "Date Source:",
        result.date_source,
    )

    print(
        "Structured Event:",
        result.structured_event_found,
    )

    print(
        "Time:",
        result.event_time,
    )

    print(
        "Location:",
        result.event_location,
    )

    print(
        "Venue:",
        result.event_venue,
    )

    print(
        "City:",
        result.event_city,
    )

    print(
        "State:",
        result.event_state,
    )

    print(
        "Country:",
        result.event_country,
    )

    print(
        "Mode:",
        result.event_mode,
    )

    print(
        "Organizer:",
        result.event_organizer,
    )

    print(
        "Type:",
        result.event_type,
    )

    print(
        "Price:",
        result.event_price,
    )

    print(
        "Registration:",
        result.registration_url,
    )

    print(
        "Score:",
        verification_score(result),
    )

    print(
        "Is Today:",
        event_is_today(
            result.detected_dates
        ),
    )

    print("=" * 60)
