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

MINIMUM_ACCEPT_SCORE = 40


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

    # Final validation
    is_india_event: bool = False
    is_cyber_event: bool = False
    is_event_page: bool = False

    # Rejection explanation
    rejected_reason: str = ""

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

    # Accuracy metadata
    date_source: str = ""
    location_source: str = ""
    structured_event_found: bool = False

    # Verification score
    score: int = 0


# ============================================================
# CYBERSECURITY KEYWORDS
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
    "cloud cybersecurity",
    "security operations",
    "soc analyst",
    "security operations center",
    "penetration testing",
    "penetration test",
    "pentesting",
    "ethical hacking",
    "ethical hacker",
    "vulnerability assessment",
    "vulnerability",
    "vulnerabilities",
    "vapt",
    "bug bounty",
    "threat intelligence",
    "incident response",
    "digital forensics",
    "cyber forensics",
    "malware analysis",
    "malware",
    "ransomware",
    "zero trust",
    "identity security",
    "identity and access management",
    "iam security",
    "devsecops",
    "secure coding",
    "data security",
    "security testing",
    "cyber risk",
    "cyber risk management",
    "grc",
    "governance risk compliance",
    "governance, risk and compliance",
    "security compliance",
    "security audit",
    "cyber threat",
    "threat hunting",
    "digital security",
    "cyber crime",
    "cybercrime",
    "cyber law",
    "cyber awareness",
    "security architecture",
    "security engineering",
    "security conference",
    "cyber conference",
)


# ============================================================
# EVENT KEYWORDS
# ============================================================

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
    "masterclass",
    "session",
    "talk",
    "roadshow",
)


# ============================================================
# INDIA LOCATIONS
# ============================================================

INDIA_KEYWORDS = (
    "india",
    "indian",
    "hyderabad",
    "secunderabad",
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
    "lucknow",
    "chandigarh",
    "indore",
    "bhubaneswar",
    "visakhapatnam",
    "vijayawada",
    "surat",
    "nagpur",
    "mysore",
    "mysuru",
    "telangana",
    "karnataka",
    "tamil nadu",
    "maharashtra",
    "delhi ncr",
    "kerala",
    "gujarat",
    "rajasthan",
    "uttar pradesh",
    "west bengal",
    "odisha",
    "punjab",
    "madhya pradesh",
    "andhra pradesh",
)


# ============================================================
# FOREIGN LOCATIONS
# ============================================================

NON_INDIA_COUNTRIES = (
    "united states",
    "united states of america",
    "usa",
    "u.s.a",
    "u.s.",
    "america",
    "canada",
    "united kingdom",
    "uk",
    "england",
    "scotland",
    "wales",
    "australia",
    "new zealand",
    "singapore",
    "malaysia",
    "germany",
    "france",
    "portugal",
    "israel",
    "ireland",
    "netherlands",
    "belgium",
    "switzerland",
    "spain",
    "italy",
    "japan",
    "china",
    "south korea",
    "brazil",
    "mexico",
    "south africa",
    "uae",
    "united arab emirates",
)


# ============================================================
# ONLINE / REMOTE KEYWORDS
# ============================================================

ONLINE_KEYWORDS = (
    "online",
    "virtual",
    "remote",
    "virtual conference",
    "virtual event",
    "online event",
    "online webinar",
    "remote event",
    "remote conference",
    "zoom",
    "webex",
    "microsoft teams",
    "google meet",
)


# ============================================================
# REGISTRATION KEYWORDS
# ============================================================

REGISTRATION_KEYWORDS = (
    "register",
    "registration",
    "rsvp",
    "tickets",
    "ticket",
    "book now",
    "sign up",
    "signup",
    "join now",
    "attend",
    "reserve",
)


# ============================================================
# KNOWN INDIAN CITIES
# ============================================================

CITY_STATE_COUNTRY = (
    ("Hyderabad", "Telangana", "India"),
    ("Secunderabad", "Telangana", "India"),
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
    ("Thiruvananthapuram", "Kerala", "India"),
    ("Lucknow", "Uttar Pradesh", "India"),
    ("Chandigarh", "Chandigarh", "India"),
    ("Indore", "Madhya Pradesh", "India"),
    ("Bhubaneswar", "Odisha", "India"),
    ("Visakhapatnam", "Andhra Pradesh", "India"),
    ("Vijayawada", "Andhra Pradesh", "India"),
    ("Surat", "Gujarat", "India"),
    ("Nagpur", "Maharashtra", "India"),
    ("Mysore", "Karnataka", "India"),
    ("Mysuru", "Karnataka", "India"),
)


# ============================================================
# DATE PATTERNS
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


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_value(value: object) -> str:
    if value is None:
        return ""

    text = str(value)

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    text = re.sub(
        r"(,\s*){2,}",
        ", ",
        text,
    )

    return text.strip(
        " \t\r\n:|-–—,."
    )


def normalize_text(value: object) -> str:
    return re.sub(
        r"\s+",
        " ",
        clean_value(value),
    ).strip()


def contains_keyword(
    text: str,
    keywords: tuple[str, ...],
) -> bool:

    lowered = text.lower()

    return any(
        keyword.lower() in lowered
        for keyword in keywords
    )


def keyword_count(
    text: str,
    keywords: tuple[str, ...],
) -> int:

    lowered = text.lower()

    return sum(
        1
        for keyword in keywords
        if keyword.lower() in lowered
    )


def today_india() -> date:
    return datetime.now(
        INDIA_TIMEZONE
    ).date()


def dedupe_preserve_order(
    values: list[str],
) -> list[str]:

    result = []
    seen = set()

    for value in values:

        value = clean_value(value)

        if not value:
            continue

        key = value.lower()

        if key in seen:
            continue

        seen.add(key)
        result.append(value)

    return result


def clean_title(
    title: str,
) -> str:

    title = clean_value(title)

    if not title:
        return ""

    bad_titles = (
        "skip to content",
        "skip to main content",
        "home",
        "menu",
        "search",
        "login",
        "sign in",
        "register",
        "events",
        "event",
    )

    if title.lower() in bad_titles:
        return ""

    title = re.sub(
        r"\s*[|•·]\s*"
        r"(home|events|meetup|eventbrite).*$",
        "",
        title,
        flags=re.IGNORECASE,
    )

    return clean_value(title)


# ============================================================
# DATE PARSING
# ============================================================

def parse_date(
    value: str,
) -> date | None:

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

            return datetime.strptime(
                value,
                fmt,
            ).date()

        except ValueError:
            continue

    return None


def iso_to_date(
    value: object,
) -> date | None:

    if not value:
        return None

    text = str(value).strip()

    try:

        return datetime.fromisoformat(
            text.replace(
                "Z",
                "+00:00",
            )
        ).date()

    except ValueError:
        pass

    try:

        return date.fromisoformat(
            text[:10]
        )

    except ValueError:
        pass

    return parse_date(text)


def expand_date_range(
    value: str,
) -> list[date]:

    value = clean_value(value)

    results = []

    # Example:
    # 4-5 September 2026

    match = re.search(
        rf"\b(\d{{1,2}})\s*[-–]\s*"
        rf"(\d{{1,2}})\s+"
        rf"({MONTHS})\s+"
        rf"(\d{{4}})\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:

        start_day = int(
            match.group(1)
        )

        end_day = int(
            match.group(2)
        )

        month = match.group(3)

        year = int(
            match.group(4)
        )

        for day_number in range(
            start_day,
            end_day + 1,
        ):

            parsed = parse_date(
                f"{day_number} "
                f"{month} "
                f"{year}"
            )

            if parsed:
                results.append(
                    parsed
                )

        return results

    # Example:
    # September 4-5, 2026

    match = re.search(
        rf"\b({MONTHS})\s+"
        rf"(\d{{1,2}})\s*[-–]\s*"
        rf"(\d{{1,2}}),\s*"
        rf"(\d{{4}})\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:

        month = match.group(1)

        start_day = int(
            match.group(2)
        )

        end_day = int(
            match.group(3)
        )

        year = int(
            match.group(4)
        )

        for day_number in range(
            start_day,
            end_day + 1,
        ):

            parsed = parse_date(
                f"{month} "
                f"{day_number}, "
                f"{year}"
            )

            if parsed:
                results.append(
                    parsed
                )

        return results

    return []


def extract_dates_from_text(
    text: str,
) -> list[date]:

    dates = []

    # First handle ranges.
    for match in re.finditer(
        rf"\b\d{{1,2}}\s*[-–]\s*\d{{1,2}}\s+"
        rf"(?:{MONTHS})\s+\d{{4}}\b",
        text,
        flags=re.IGNORECASE,
    ):

        dates.extend(
            expand_date_range(
                match.group(0)
            )
        )

    for match in re.finditer(
        rf"\b(?:{MONTHS})\s+\d{{1,2}}\s*[-–]\s*"
        rf"\d{{1,2}},\s*\d{{4}}\b",
        text,
        flags=re.IGNORECASE,
    ):

        dates.extend(
            expand_date_range(
                match.group(0)
            )
        )

    # Normal dates.
    for pattern in DATE_PATTERNS:

        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):

            parsed = parse_date(
                match.group(0)
            )

            if parsed:
                dates.append(
                    parsed
                )

    # Deduplicate.
    unique_dates = sorted(
        set(dates)
    )

    return unique_dates


def format_date(
    value: date | None,
) -> str:

    if not value:
        return ""

    return value.strftime(
        "%d %B %Y"
    )


# ============================================================
# JSON-LD / STRUCTURED DATA
# ============================================================

def parse_json_ld(
    soup: BeautifulSoup,
) -> list[dict]:

    events = []

    scripts = soup.find_all(
        "script",
        attrs={
            "type": "application/ld+json"
        },
    )

    for script in scripts:

        raw = script.string

        if not raw:
            raw = script.get_text(
                strip=True
            )

        if not raw:
            continue

        try:

            data = json.loads(
                raw
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):

            continue

        objects = []

        if isinstance(
            data,
            dict,
        ):

            objects.append(
                data
            )

            graph = data.get(
                "@graph"
            )

            if isinstance(
                graph,
                list,
            ):

                objects.extend(
                    graph
                )

        elif isinstance(
            data,
            list,
        ):

            objects.extend(
                data
            )

        for item in objects:

            if not isinstance(
                item,
                dict,
            ):
                continue

            item_type = item.get(
                "@type",
                ""
            )

            if isinstance(
                item_type,
                list,
            ):

                item_types = [
                    str(x).lower()
                    for x in item_type
                ]

            else:

                item_types = [
                    str(item_type).lower()
                ]

            if (
                "event" in item_types
                or any(
                    "event" in value
                    for value in item_types
                )
            ):

                events.append(
                    item
                )

    return events


def first_structured_event(
    events: list[dict],
) -> dict:

    if not events:
        return {}

    # Prefer a complete Event object.
    for event in events:

        if (
            event.get("startDate")
            or event.get("location")
            or event.get("name")
        ):

            return event

    return events[0]


# ============================================================
# STRUCTURED DATE EXTRACTION
# ============================================================

def extract_structured_dates(
    event: dict,
) -> tuple[list[date], str, str]:

    dates = []

    start_date = event.get(
        "startDate"
    )

    end_date = event.get(
        "endDate"
    )

    start = iso_to_date(
        start_date
    )

    end = iso_to_date(
        end_date
    )

    if start:
        dates.append(
            start
        )

    if end:
        dates.append(
            end
        )

    return (
        sorted(set(dates)),
        format_date(start),
        format_date(end),
    )


# ============================================================
# LOCATION EXTRACTION
# ============================================================

def location_to_text(
    location: object,
) -> str:

    if isinstance(
        location,
        str,
    ):

        return clean_value(
            location
        )

    if not isinstance(
        location,
        dict,
    ):

        return ""

    parts = []

    name = clean_value(
        location.get(
            "name",
            ""
        )
    )

    address = location.get(
        "address",
        ""
    )

    if name:
        parts.append(
            name
        )

    if isinstance(
        address,
        dict,
    ):

        for key in (
            "streetAddress",
            "addressLocality",
            "addressRegion",
            "postalCode",
            "addressCountry",
        ):

            value = clean_value(
                address.get(
                    key,
                    ""
                )
            )

            if value:
                parts.append(
                    value
                )

    elif address:

        parts.append(
            clean_value(
                address
            )
        )

    return ", ".join(
        dedupe_preserve_order(
            parts
        )
    )


def extract_location_from_structured(
    event: dict,
) -> tuple[str, str, str, str, str]:

    location = event.get(
        "location"
    )

    if isinstance(
        location,
        list,
    ):

        location = (
            location[0]
            if location
            else {}
        )

    location_text = location_to_text(
        location
    )

    venue = ""
    city = ""
    state = ""
    country = ""

    if isinstance(
        location,
        dict,
    ):

        venue = clean_value(
            location.get(
                "name",
                ""
            )
        )

        address = location.get(
            "address",
            {}
        )

        if isinstance(
            address,
            dict,
        ):

            city = clean_value(
                address.get(
                    "addressLocality",
                    ""
                )
            )

            state = clean_value(
                address.get(
                    "addressRegion",
                    ""
                )
            )

            country_value = address.get(
                "addressCountry",
                ""
            )

            if isinstance(
                country_value,
                dict,
            ):

                country = clean_value(
                    country_value.get(
                        "name",
                        ""
                    )
                )

            else:

                country = clean_value(
                    country_value
                )

    return (
        location_text,
        venue,
        city,
        state,
        country,
    )


# ============================================================
# MODE DETECTION
# ============================================================

def detect_event_mode(
    text: str,
    structured_event: dict,
    location_text: str,
) -> str:

    text_lower = text.lower()

    structured_location = (
        structured_event.get(
            "location"
        )
        if structured_event
        else None
    )

    if isinstance(
        structured_location,
        dict,
    ):

        location_type = str(
            structured_location.get(
                "@type",
                ""
            )
        ).lower()

        if "virtual" in location_type:

            return "Online"

        if "virtualLocation" in location_type:

            return "Online"

    if contains_keyword(
        location_text,
        ONLINE_KEYWORDS,
    ):

        return "Online"

    online_count = keyword_count(
        text_lower,
        ONLINE_KEYWORDS,
    )

    physical_count = 0

    for keyword in (
        "venue",
        "address",
        "street",
        "hall",
        "auditorium",
        "hotel",
        "campus",
        "office",
    ):

        if keyword in text_lower:
            physical_count += 1

    if (
        online_count >= 2
        and physical_count == 0
    ):

        return "Online"

    if (
        online_count > 0
        and physical_count > 0
    ):

        return "Hybrid"

    return "Offline"


# ============================================================
# TIME EXTRACTION
# ============================================================

TIME_PATTERNS = (
    r"\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b",
    r"\b\d{1,2}\s*(?:AM|PM|am|pm)\b",
)


def extract_time(
    text: str,
) -> str:

    values = []

    for pattern in TIME_PATTERNS:

        matches = re.findall(
            pattern,
            text,
        )

        values.extend(
            matches
        )

    values = dedupe_preserve_order(
        values
    )

    if not values:
        return ""

    if len(values) > 4:
        values = values[:4]

    return " – ".join(
        values
    )


# ============================================================
# ORGANIZER EXTRACTION
# ============================================================

def extract_organizer(
    text: str,
    structured_event: dict,
) -> str:

    organizer = structured_event.get(
        "organizer"
    )

    if isinstance(
        organizer,
        dict,
    ):

        name = clean_value(
            organizer.get(
                "name",
                ""
            )
        )

        if name:
            return name

    if isinstance(
        organizer,
        list,
    ):

        for item in organizer:

            if isinstance(
                item,
                dict,
            ):

                name = clean_value(
                    item.get(
                        "name",
                        ""
                    )
                )

                if name:
                    return name

            elif item:

                return clean_value(
                    item
                )

    if isinstance(
        organizer,
        str,
    ):

        organizer = clean_value(
            organizer
        )

        if organizer:
            return organizer

    patterns = (
        r"(?:organized|hosted|presented|conducted)\s+by\s+"
        r"([A-Z][A-Za-z0-9&.,' -]{2,80})",
        r"(?:organizer|organised by|organized by)\s*[:\-]\s*"
        r"([A-Z][A-Za-z0-9&.,' -]{2,80})",
    )

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:

            return clean_value(
                match.group(1)
            )

    return ""


# ============================================================
# EVENT TYPE
# ============================================================

def extract_event_type(
    title: str,
    text: str,
    structured_event: dict,
) -> str:

    event_type = structured_event.get(
        "@type",
        ""
    )

    if isinstance(
        event_type,
        list,
    ):

        for value in event_type:

            value = clean_value(
                value
            )

            if (
                value
                and value.lower() != "event"
            ):

                return value

    elif event_type:

        value = clean_value(
            event_type
        )

        if (
            value
            and value.lower() != "event"
        ):

            return value

    combined = (
        f"{title} {text}"
    ).lower()

    for keyword in (
        "webinar",
        "conference",
        "summit",
        "workshop",
        "meetup",
        "hackathon",
        "training",
        "seminar",
        "symposium",
        "masterclass",
        "bootcamp",
        "roadshow",
    ):

        if keyword in combined:
            return keyword.title()

    return "Event"


# ============================================================
# PRICE EXTRACTION
# ============================================================

def extract_price(
    text: str,
    structured_event: dict,
) -> str:

    offers = structured_event.get(
        "offers"
    )

    if isinstance(
        offers,
        dict,
    ):

        price = clean_value(
            offers.get(
                "price",
                ""
            )
        )

        currency = clean_value(
            offers.get(
                "priceCurrency",
                ""
            )
        )

        if price:

            if currency:
                return (
                    f"{currency} {price}"
                )

            return price

    if isinstance(
        offers,
        list,
    ):

        for offer in offers:

            if not isinstance(
                offer,
                dict,
            ):
                continue

            price = clean_value(
                offer.get(
                    "price",
                    ""
                )
            )

            currency = clean_value(
                offer.get(
                    "priceCurrency",
                    ""
                )
            )

            if price:

                if currency:
                    return (
                        f"{currency} {price}"
                    )

                return price

    lowered = text.lower()

    if re.search(
        r"\bfree\b",
        lowered,
    ):

        return "Free"

    match = re.search(
        r"(?:₹|rs\.?|inr)\s*[\d,]+(?:\.\d+)?",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        return clean_value(
            match.group(0)
        )

    match = re.search(
        r"\b\d[\d,]*(?:\.\d+)?\s*(?:usd|inr|eur|gbp)\b",
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
    page_url: str,
) -> str:

    for link in soup.find_all(
        "a",
        href=True,
    ):

        href = link.get(
            "href",
            ""
        )

        label = link.get_text(
            " ",
            strip=True,
        )

        combined = (
            f"{label} {href}"
        ).lower()

        if any(
            keyword in combined
            for keyword in REGISTRATION_KEYWORDS
        ):

            absolute = urljoin(
                page_url,
                href,
            )

            if absolute.startswith(
                (
                    "http://",
                    "https://",
                )
            ):

                return absolute

    return ""


# ============================================================
# EVENT URL
# ============================================================

def extract_event_url(
    structured_event: dict,
    page_url: str,
) -> str:

    url = structured_event.get(
        "url"
    )

    if url:

        url = urljoin(
            page_url,
            str(url).strip(),
        )

        if url.startswith(
            (
                "http://",
                "https://",
            )
        ):

            return url

    return page_url


# ============================================================
# DESCRIPTION
# ============================================================

def extract_description(
    soup: BeautifulSoup,
    structured_event: dict,
) -> str:

    description = clean_value(
        structured_event.get(
            "description",
            ""
        )
    )

    if description:
        return description

    meta = soup.find(
        "meta",
        attrs={
            "name": "description"
        },
    )

    if meta:

        description = clean_value(
            meta.get(
                "content",
                ""
            )
        )

        if description:
            return description

    paragraph_text = []

    for paragraph in soup.find_all(
        "p"
    )[:10]:

        text = clean_value(
            paragraph.get_text(
                " ",
                strip=True,
            )
        )

        if len(text) >= 40:

            paragraph_text.append(
                text
            )

    return " ".join(
        paragraph_text[:3]
    )


# ============================================================
# LOCATION VALIDATION
# ============================================================

def detect_india_location(
    location_text: str,
    page_text: str,
    event_mode: str,
    event_country: str = "",
) -> tuple[bool, str]:

    location_lower = (
        f"{location_text} "
        f"{event_country}"
    ).lower()

    page_lower = page_text.lower()

    # Online events can be international.
    if event_mode == "Online":

        return (
            True,
            "Online/remote event - international events allowed",
        )

    # Hybrid must have an Indian physical component.
    if event_mode == "Hybrid":

        if (
            contains_keyword(
                location_lower,
                INDIA_KEYWORDS,
            )
            or contains_keyword(
                page_lower,
                INDIA_KEYWORDS,
            )
        ):

            return (
                True,
                "Hybrid event has Indian location",
            )

        if contains_keyword(
            location_lower,
            NON_INDIA_COUNTRIES,
        ):

            return (
                False,
                "Hybrid event appears outside India",
            )

        return (
            False,
            "Hybrid event has no verified Indian location",
        )

    # Physical Indian city.
    for city, state, country in CITY_STATE_COUNTRY:

        if city.lower() in location_lower:

            return (
                True,
                f"Indian city detected: {city}",
            )

    # Explicit India.
    if "india" in location_lower:

        return (
            True,
            "India explicitly detected in location",
        )

    # Indian state.
    for keyword in INDIA_KEYWORDS:

        if keyword in location_lower:

            return (
                True,
                f"Indian location detected: {keyword}",
            )

    # Foreign physical location.
    for country in NON_INDIA_COUNTRIES:

        if country in location_lower:

            return (
                False,
                f"Foreign physical location detected: {country}",
            )

    # Do NOT accept India merely because it appears
    # somewhere unrelated on the page.
    return (
        False,
        "Physical event has no verified Indian location",
    )


# ============================================================
# DATE VALIDATION
# ============================================================

def validate_dates(
    detected_dates: list[date],
) -> tuple[bool, bool, str]:

    today = today_india()

    if not detected_dates:

        return (
            False,
            False,
            "No event date detected",
        )

    future_or_today = any(
        value >= today
        for value in detected_dates
    )

    if not future_or_today:

        return (
            True,
            False,
            "All detected event dates are in the past",
        )

    return (
        True,
        True,
        "",
    )


# ============================================================
# DATE EXTRACTION FOCUS
# ============================================================

def extract_event_dates(
    soup: BeautifulSoup,
    structured_event: dict,
) -> tuple[list[date], str]:

    # Strongest source: Schema.org.
    structured_dates, start_text, end_text = (
        extract_structured_dates(
            structured_event
        )
    )

    if structured_dates:

        return (
            structured_dates,
            "Schema.org/Event structured data",
        )

    # Search focused event-related areas first.
    focused_parts = []

    for selector in (
        "time",
        "[datetime]",
        ".event-date",
        ".event-date-time",
        ".date",
        ".datetime",
        ".start-date",
        ".end-date",
        ".event-details",
        ".event-info",
        "main",
    ):

        try:

            elements = soup.select(
                selector
            )

        except Exception:
            elements = []

        for element in elements[:20]:

            text = clean_value(
                element.get_text(
                    " ",
                    strip=True,
                )
            )

            if text:
                focused_parts.append(
                    text
                )

            datetime_value = element.get(
                "datetime"
            )

            if datetime_value:
                focused_parts.append(
                    str(datetime_value)
                )

    focused_text = " ".join(
        focused_parts
    )

    focused_dates = extract_dates_from_text(
        focused_text
    )

    if focused_dates:

        return (
            focused_dates,
            "Focused event page content",
        )

    # Last fallback: page text.
    page_text = clean_value(
        soup.get_text(
            " ",
            strip=True,
        )
    )

    dates = extract_dates_from_text(
        page_text
    )

    return (
        dates,
        "Page text fallback",
    )


# ============================================================
# SCORE
# ============================================================

def calculate_score(
    result: VerificationResult,
) -> int:

    score = 0

    # Reachability.
    if result.reachable:
        score += 10

    # Strong structured event data.
    if result.structured_event_found:
        score += 25

    # Cybersecurity relevance.
    if result.has_cyber_signal:
        score += 20

    # Recognizable event.
    if result.has_event_signal:
        score += 10

    # Date.
    if result.has_date_signal:
        score += 10

    # Future/today date.
    if result.has_future_date:
        score += 5

    # Registration.
    if result.has_registration_signal:
        score += 5

    # Location.
    if result.has_location_signal:
        score += 5

    # Verified India physical/hybrid.
    if result.has_india_location:
        score += 5

    # Online event gets a smaller location-related confidence
    # because international online events are allowed.
    if (
        result.has_online_signal
        and result.event_mode == "Online"
    ):

        score += 5

    # Strong final validation.
    if result.is_cyber_event:
        score += 5

    if result.is_event_page:
        score += 5

    # --------------------------------------------------------
    # Hard safety caps
    # --------------------------------------------------------

    if not result.is_cyber_event:
        score = min(
            score,
            25,
        )

    if not result.is_event_page:
        score = min(
            score,
            30,
        )

    if not result.has_date_signal:
        score = min(
            score,
            30,
        )

    if (
        result.event_mode != "Online"
        and not result.has_india_location
    ):

        score = min(
            score,
            35,
        )

    if (
        result.rejected_reason
        and not result.is_cyber_event
    ):

        score = min(
            score,
            25,
        )

    return max(
        0,
        min(
            100,
            score,
        ),
    )


# ============================================================
# VERIFICATION SCORE HELPER
# ============================================================

def verification_score(
    result: VerificationResult,
) -> int:
    """
    Return the final verification score.

    pipeline.py imports this function directly.
    """

    if not isinstance(
        result,
        VerificationResult,
    ):

        return 0

    return int(
        getattr(
            result,
            "score",
            0,
        )
    )


# ============================================================
# VERIFY EVENT
# ============================================================

def verify_event(
    url: str,
) -> VerificationResult:

    result = VerificationResult()

    if not url:
        result.rejected_reason = (
            "Empty URL"
        )
        return result

    if not url.startswith(
        (
            "http://",
            "https://",
        )
    ):

        result.rejected_reason = (
            "Invalid URL"
        )

        return result

    # --------------------------------------------------------
    # Fetch page
    # --------------------------------------------------------

    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()

    except requests.RequestException as exc:

        result.rejected_reason = (
            f"Page unreachable: {exc}"
        )

        return result

    result.reachable = True

    final_url = response.url or url

    # --------------------------------------------------------
    # Parse HTML
    # --------------------------------------------------------

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    # Remove noise.
    for element in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
        ]
    ):

        element.decompose()

    page_text = clean_value(
        soup.get_text(
            " ",
            strip=True,
        )
    )

    result.text = page_text

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    title = ""

    if soup.title:

        title = clean_title(
            soup.title.get_text(
                " ",
                strip=True,
            )
        )

    if not title:

        h1 = soup.find(
            "h1"
        )

        if h1:

            title = clean_title(
                h1.get_text(
                    " ",
                    strip=True,
                )
            )

    result.title = title

    # --------------------------------------------------------
    # JSON-LD
    # --------------------------------------------------------

    structured_events = parse_json_ld(
        BeautifulSoup(
            response.text,
            "html.parser",
        )
    )

    structured_event = first_structured_event(
        structured_events
    )

    result.structured_event_found = bool(
        structured_event
    )

    # --------------------------------------------------------
    # Basic combined text
    # --------------------------------------------------------

    combined_text = (
        f"{result.title} "
        f"{page_text}"
    )

    # --------------------------------------------------------
    # Event relevance
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Structured title/name can be stronger.
    # --------------------------------------------------------

    structured_name = clean_value(
        structured_event.get(
            "name",
            ""
        )
    )

    if structured_name:

        if contains_keyword(
            structured_name,
            CYBER_KEYWORDS,
        ):

            result.has_cyber_signal = True

        if contains_keyword(
            structured_name,
            EVENT_KEYWORDS,
        ):

            result.has_event_signal = True

    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    detected_dates, date_source = (
        extract_event_dates(
            soup,
            structured_event,
        )
    )

    result.detected_dates = [
        format_date(value)
        for value in detected_dates
    ]

    result.date_source = date_source

    (
        result.has_date_signal,
        result.has_future_date,
        date_reason,
    ) = validate_dates(
        detected_dates
    )

    if detected_dates:

        result.event_date = format_date(
            detected_dates[0]
        )

        if len(detected_dates) > 1:

            result.event_end_date = format_date(
                detected_dates[-1]
            )

    # --------------------------------------------------------
    # Location
    # --------------------------------------------------------

    (
        structured_location,
        structured_venue,
        structured_city,
        structured_state,
        structured_country,
    ) = extract_location_from_structured(
        structured_event
    )

    result.event_location = (
        structured_location
    )

    result.event_venue = (
        structured_venue
    )

    result.event_city = (
        structured_city
    )

    result.event_state = (
        structured_state
    )

    result.event_country = (
        structured_country
    )

    result.location_source = (
        "Schema.org/Event structured data"
        if structured_location
        else "Page content"
    )

    # --------------------------------------------------------
    # Fallback location extraction
    # --------------------------------------------------------

    if not result.event_location:

        location_patterns = (
            r"(?:where|location|venue)\s*[:\-]\s*"
            r"([^|]{5,180})",
            r"(?:address)\s*[:\-]\s*"
            r"([^|]{5,180})",
        )

        for pattern in location_patterns:

            match = re.search(
                pattern,
                page_text,
                flags=re.IGNORECASE,
            )

            if match:

                candidate_location = clean_value(
                    match.group(1)
                )

                # Avoid navigation garbage.
                if (
                    len(candidate_location) <= 180
                    and not candidate_location.lower().startswith(
                        (
                            "skip to",
                            "login",
                            "sign in",
                        )
                    )
                ):

                    result.event_location = (
                        candidate_location
                    )

                    result.location_source = (
                        "Focused page content"
                    )

                    break

    # --------------------------------------------------------
    # Event mode
    # --------------------------------------------------------

    result.event_mode = detect_event_mode(
        combined_text,
        structured_event,
        result.event_location,
    )

    result.has_online_signal = (
        result.event_mode
        in (
            "Online",
            "Hybrid",
        )
    )

    # --------------------------------------------------------
    # Location signal
    # --------------------------------------------------------

    result.has_location_signal = bool(
        result.event_location
        or result.event_city
        or result.event_state
        or result.event_country
    )

    # --------------------------------------------------------
    # India validation
    # --------------------------------------------------------

    (
        india_valid,
        india_reason,
    ) = detect_india_location(
        result.event_location,
        page_text,
        result.event_mode,
        result.event_country,
    )

    result.has_india_location = (
        india_valid
    )

    result.is_india_event = (
        india_valid
    )

    # --------------------------------------------------------
    # Time
    # --------------------------------------------------------

    if structured_event.get(
        "startDate"
    ):

        start_datetime = str(
            structured_event.get(
                "startDate"
            )
        )

        time_match = re.search(
            r"T(\d{1,2}:\d{2})",
            start_datetime,
        )

        if time_match:

            result.event_time = (
                time_match.group(1)
            )

    if not result.event_time:

        result.event_time = extract_time(
            page_text
        )

    # --------------------------------------------------------
    # Venue fallback
    # --------------------------------------------------------

    if not result.event_venue:

        if (
            result.event_location
            and result.event_mode
            != "Online"
        ):

            first_part = (
                result.event_location.split(
                    ","
                )[0].strip()
            )

            if (
                first_part
                and len(first_part) <= 100
            ):

                result.event_venue = (
                    first_part
                )

    # --------------------------------------------------------
    # Organizer
    # --------------------------------------------------------

    result.event_organizer = (
        extract_organizer(
            page_text,
            structured_event,
        )
    )

    # --------------------------------------------------------
    # Event type
    # --------------------------------------------------------

    result.event_type = (
        extract_event_type(
            result.title,
            page_text,
            structured_event,
        )
    )

    # --------------------------------------------------------
    # Price
    # --------------------------------------------------------

    result.event_price = (
        extract_price(
            page_text,
            structured_event,
        )
    )

    # --------------------------------------------------------
    # Registration
    # --------------------------------------------------------

    result.registration_url = (
        extract_registration_url(
            soup,
            final_url,
        )
    )

    result.has_registration_signal = bool(
        result.registration_url
        or contains_keyword(
            page_text,
            REGISTRATION_KEYWORDS,
        )
    )

    # --------------------------------------------------------
    # Event URL
    # --------------------------------------------------------

    result.event_url = (
        extract_event_url(
            structured_event,
            final_url,
        )
    )

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    result.event_description = (
        extract_description(
            soup,
            structured_event,
        )
    )

    # --------------------------------------------------------
    # Final cybersecurity validation
    # --------------------------------------------------------

    # Require meaningful cybersecurity relevance.
    cyber_keyword_hits = keyword_count(
        (
            f"{result.title} "
            f"{result.event_description} "
            f"{page_text[:12000]}"
        ),
        CYBER_KEYWORDS,
    )

    result.is_cyber_event = (
        result.has_cyber_signal
        and cyber_keyword_hits >= 1
    )

    # --------------------------------------------------------
    # Final event-page validation
    # --------------------------------------------------------

    # A page should have multiple event indicators.
    event_keyword_hits = keyword_count(
        (
            f"{result.title} "
            f"{result.event_type} "
            f"{page_text[:12000]}"
        ),
        EVENT_KEYWORDS,
    )

    result.is_event_page = (
        result.has_event_signal
        and (
            event_keyword_hits >= 1
            or result.structured_event_found
        )
    )

    # --------------------------------------------------------
    # Hard rejection rules
    # --------------------------------------------------------

    if not result.is_cyber_event:

        result.rejected_reason = (
            "Not sufficiently related to cybersecurity"
        )

    elif not result.is_event_page:

        result.rejected_reason = (
            "Page does not appear to be a real event page"
        )

    elif not result.has_date_signal:

        result.rejected_reason = (
            "Event date could not be verified"
        )

    elif not result.has_future_date:

        result.rejected_reason = (
            "Event date is in the past"
        )

    elif (
        result.event_mode != "Online"
        and not result.has_india_location
    ):

        result.rejected_reason = (
            india_reason
        )

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    result.score = calculate_score(
        result
    )

    # --------------------------------------------------------
    # Additional safety cap
    # --------------------------------------------------------

    if result.rejected_reason:

        result.score = min(
            result.score,
            35,
        )

    return result


# ============================================================
# TODAY CHECK
# ============================================================

def event_is_today(
    result: VerificationResult,
) -> bool:

    if not result.detected_dates:
        return False

    today = today_india()

    parsed_dates = []

    for value in result.detected_dates:

        parsed = parse_date(
            value
        )

        if parsed:

            parsed_dates.append(
                parsed
            )

    if not parsed_dates:
        return False

    if today in parsed_dates:
        return True

    return (
        min(parsed_dates)
        <= today
        <= max(parsed_dates)
    )


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":

    import sys

    print()
    print("=" * 70)
    print("INDIA CYBERSECURITY EVENT VERIFIER")
    print("=" * 70)

    if len(sys.argv) < 2:

        print()
        print(
            "Usage:"
        )

        print(
            "python verifier.py "
            "https://example.com/event"
        )

        print()
        print(
            "No URL supplied."
        )

        raise SystemExit(0)

    test_url = sys.argv[1]

    print()
    print(
        f"🔎 Testing: {test_url}"
    )

    print()

    result = verify_event(
        test_url
    )

    print(
        f"Reachable: "
        f"{result.reachable}"
    )

    print(
        f"Title: "
        f"{result.title}"
    )

    print(
        f"Event: "
        f"{result.is_event_page}"
    )

    print(
        f"Cybersecurity: "
        f"{result.is_cyber_event}"
    )

    print(
        f"Mode: "
        f"{result.event_mode}"
    )

    print(
        f"Date: "
        f"{result.event_date}"
    )

    print(
        f"End date: "
        f"{result.event_end_date}"
    )

    print(
        f"Time: "
        f"{result.event_time}"
    )

    print(
        f"Location: "
        f"{result.event_location}"
    )

    print(
        f"Venue: "
        f"{result.event_venue}"
    )

    print(
        f"City: "
        f"{result.event_city}"
    )

    print(
        f"State: "
        f"{result.event_state}"
    )

    print(
        f"Country: "
        f"{result.event_country}"
    )

    print(
        f"Organizer: "
        f"{result.event_organizer}"
    )

    print(
        f"Type: "
        f"{result.event_type}"
    )

    print(
        f"Price: "
        f"{result.event_price}"
    )

    print(
        f"Registration: "
        f"{result.registration_url}"
    )

    print(
        f"Score: "
        f"{result.score}/100"
    )

    print(
        f"Today: "
        f"{event_is_today(result)}"
    )

    print(
        f"Rejected reason: "
        f"{result.rejected_reason}"
    )

    print()
    print("=" * 70)
