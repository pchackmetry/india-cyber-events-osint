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
# HELPERS
# ============================================================

def clean_value(value: object) -> str:
    if value is None:
        return ""

    text = str(value)

    text = re.sub(r"\s+", " ", text)

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

        result = []

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
                result.append(
                    parsed
                )

        return result

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

        result = []

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
                result.append(
                    parsed
                )

        return result

    parsed = parse_date(value)

    if parsed:
        return [parsed]

    return []


def dates_to_strings(
    values: list[date],
) -> list[str]:

    return [
        value.strftime(
            "%d %B %Y"
        )
        for value in sorted(
            set(values)
        )
    ]


def format_event_dates(
    detected_dates: list[str],
) -> tuple[str, str]:

    parsed = []

    for value in detected_dates:

        parsed.extend(
            expand_date_range(
                value
            )
        )

    parsed = sorted(
        set(parsed)
    )

    if not parsed:
        return "", ""

    start = parsed[0]
    end = parsed[-1]

    if start == end:

        return (
            start.strftime(
                "%d %B %Y"
            ),
            "",
        )

    return (
        start.strftime(
            "%d %B %Y"
        ),
        end.strftime(
            "%d %B %Y"
        ),
    )


def event_is_today(
    detected_dates: list[str],
) -> bool:

    if not detected_dates:
        return False

    today = today_india()

    parsed = []

    for value in detected_dates:

        parsed.extend(
            expand_date_range(
                value
            )
        )

    parsed = sorted(
        set(parsed)
    )

    if not parsed:
        return False

    return (
        min(parsed)
        <= today
        <= max(parsed)
    )


def has_future_date(
    detected_dates: list[str],
) -> bool:

    if not detected_dates:
        return False

    today = today_india()

    for value in detected_dates:

        for parsed in expand_date_range(
            value
        ):

            if parsed >= today:
                return True

    return False


# ============================================================
# JSON-LD
# ============================================================

def iter_json_objects(
    value: object,
):

    if isinstance(
        value,
        dict,
    ):

        yield value

        for child in value.values():

            yield from iter_json_objects(
                child
            )

    elif isinstance(
        value,
        list,
    ):

        for child in value:

            yield from iter_json_objects(
                child
            )


def is_event_type(
    value: object,
) -> bool:

    if isinstance(
        value,
        str,
    ):

        lowered = value.lower()

        return (
            lowered == "event"
            or lowered.endswith(
                "event"
            )
        )

    if isinstance(
        value,
        list,
    ):

        return any(
            is_event_type(item)
            for item in value
        )

    return False


def extract_jsonld_events(
    soup: BeautifulSoup,
) -> list[dict]:

    events = []

    for script in soup.find_all(
        "script",
        attrs={
            "type": re.compile(
                r"application/ld\+json",
                re.IGNORECASE,
            )
        },
    ):

        raw = (
            script.string
            or script.get_text()
        )

        if not raw:
            continue

        try:

            data = json.loads(
                raw.strip()
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            continue

        for obj in iter_json_objects(
            data
        ):

            if not isinstance(
                obj,
                dict,
            ):
                continue

            if is_event_type(
                obj.get("@type")
            ):
                events.append(obj)

    return events


def jsonld_address(
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

    address = location.get(
        "address"
    )

    if isinstance(
        address,
        str,
    ):

        return clean_value(
            address
        )

    parts = []

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

            value = address.get(
                key
            )

            if value:

                parts.append(
                    clean_value(
                        value
                    )
                )

    if not parts:

        for key in (
            "name",
            "streetAddress",
            "addressLocality",
            "addressRegion",
            "addressCountry",
        ):

            value = location.get(
                key
            )

            if value:

                parts.append(
                    clean_value(
                        value
                    )
                )

    return ", ".join(
        dedupe_preserve_order(
            parts
        )
    )


def extract_structured_event(
    events: list[dict],
) -> dict:

    if not events:
        return {}

    today = today_india()

    candidates = []

    for event in events:

        score = 0

        start = iso_to_date(
            event.get(
                "startDate"
            )
        )

        end = (
            iso_to_date(
                event.get(
                    "endDate"
                )
            )
            or start
        )

        if start:

            score += 40

            if (
                end
                and start <= today <= end
            ):

                score += 100

            elif start >= today:

                score += 50

        if event.get(
            "location"
        ):

            score += 20

        if event.get(
            "name"
        ):

            score += 20

        if event.get(
            "organizer"
        ):

            score += 10

        candidates.append(
            (
                score,
                event,
            )
        )

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return candidates[0][1]


# ============================================================
# STRUCTURED EVENT FIELDS
# ============================================================

def apply_structured_event(
    result: VerificationResult,
    event: dict,
    response_url: str,
) -> None:

    if not event:
        return

    result.structured_event_found = True

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    structured_title = clean_title(
        event.get(
            "name",
            "",
        )
    )

    if structured_title:

        result.title = (
            structured_title
        )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    start = iso_to_date(
        event.get(
            "startDate"
        )
    )

    end = (
        iso_to_date(
            event.get(
                "endDate"
            )
        )
        or start
    )

    if start:

        dates = [start]

        if (
            end
            and end >= start
        ):

            current = start

            while current <= end:

                if current not in dates:

                    dates.append(
                        current
                    )

                if len(dates) >= 15:
                    break

                current += timedelta(
                    days=1
                )

        result.detected_dates = (
            dates_to_strings(
                dates
            )
        )

        result.event_date = (
            start.strftime(
                "%d %B %Y"
            )
        )

        if (
            end
            and end != start
        ):

            result.event_end_date = (
                end.strftime(
                    "%d %B %Y"
                )
            )

        result.date_source = (
            "JSON-LD Event"
        )

        result.has_date_signal = True

    # --------------------------------------------------------
    # Time
    # --------------------------------------------------------

    start_raw = event.get(
        "startDate"
    )

    if start_raw:

        time_match = re.search(
            r"T(\d{2}:\d{2})"
            r"(?::\d{2})?",
            str(start_raw),
        )

        if time_match:

            result.event_time = (
                time_match.group(1)
            )

    # --------------------------------------------------------
    # Location
    # --------------------------------------------------------

    location = event.get(
        "location"
    )

    if isinstance(
        location,
        dict,
    ):

        venue = clean_value(
            location.get(
                "name",
                "",
            )
        )

        address = location.get(
            "address"
        )

        city = ""
        state = ""
        country = ""
        street = ""
        postal_code = ""

        if isinstance(
            address,
            dict,
        ):

            street = clean_value(
                address.get(
                    "streetAddress",
                    "",
                )
            )

            city = clean_value(
                address.get(
                    "addressLocality",
                    "",
                )
            )

            state = clean_value(
                address.get(
                    "addressRegion",
                    "",
                )
            )

            postal_code = clean_value(
                address.get(
                    "postalCode",
                    "",
                )
            )

            country_value = (
                address.get(
                    "addressCountry",
                    "",
                )
            )

            if isinstance(
                country_value,
                dict,
            ):

                country = clean_value(
                    country_value.get(
                        "name",
                        "",
                    )
                )

            else:

                country = clean_value(
                    country_value
                )

        elif isinstance(
            address,
            str,
        ):

            address_text = clean_value(
                address
            )

            street = address_text

            (
                city,
                state,
                country,
            ) = infer_indian_city(
                address_text
            )

        parts = []

        if street:
            parts.append(
                street
            )

        if city:
            parts.append(
                city
            )

        if state:
            parts.append(
                state
            )

        if postal_code:
            parts.append(
                postal_code
            )

        if country:
            parts.append(
                country
            )

        parts = dedupe_preserve_order(
            parts
        )

        location_text = (
            ", ".join(parts)
        )

        if venue and location_text:

            result.event_location = (
                f"{venue}, "
                f"{location_text}"
            )

        elif location_text:

            result.event_location = (
                location_text
            )

        elif venue:

            result.event_location = venue

        result.event_venue = venue
        result.event_city = city
        result.event_state = state
        result.event_country = country

    elif isinstance(
        location,
        str,
    ):

        result.event_location = (
            clean_value(
                location
            )
        )

    if result.event_location:

        result.has_location_signal = True

        result.location_source = (
            "JSON-LD Event"
        )

    # --------------------------------------------------------
    # Organizer
    # --------------------------------------------------------

    organizer = event.get(
        "organizer"
    )

    if isinstance(
        organizer,
        dict,
    ):

        result.event_organizer = (
            clean_value(
                organizer.get(
                    "name",
                    "",
                )
            )
        )

    elif isinstance(
        organizer,
        str,
    ):

        result.event_organizer = (
            clean_value(
                organizer
            )
        )

    # --------------------------------------------------------
    # Event URL
    # --------------------------------------------------------

    event_url = event.get(
        "url"
    )

    if event_url:

        result.event_url = urljoin(
            response_url,
            str(event_url),
        )

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    description = event.get(
        "description"
    )

    if description:

        result.event_description = (
            clean_description(
                str(description)
            )
        )

    # --------------------------------------------------------
    # Event type
    # --------------------------------------------------------

    event_type = event.get(
        "eventType"
    )

    if isinstance(
        event_type,
        list,
    ):

        event_type = ", ".join(
            clean_value(x)
            for x in event_type
            if clean_value(x)
        )

    if event_type:

        result.event_type = (
            clean_value(
                event_type
            )
        )

    # --------------------------------------------------------
    # Price
    # --------------------------------------------------------

    offers = event.get(
        "offers"
    )

    if isinstance(
        offers,
        dict,
    ):

        price = offers.get(
            "price"
        )

        currency = clean_value(
            offers.get(
                "priceCurrency",
                "",
            )
        )

        if price is not None:

            result.event_price = (
                f"{price} {currency}"
            ).strip()


# ============================================================
# FOCUSED DATE EXTRACTION
# ============================================================

def extract_dates_from_text(
    text: str,
) -> list[str]:

    found = []

    range_patterns = (
        rf"\b\d{{1,2}}\s*[-–]\s*"
        rf"\d{{1,2}}\s+"
        rf"(?:{MONTHS})\s+"
        rf"\d{{4}}\b",

        rf"\b(?:{MONTHS})\s+"
        rf"\d{{1,2}}\s*[-–]\s*"
        rf"\d{{1,2}},\s*"
        rf"\d{{4}}\b",
    )

    for pattern in range_patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        for match in matches:

            if match not in found:

                found.append(
                    match
                )

    for pattern in DATE_PATTERNS:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        for match in matches:

            if match not in found:

                found.append(
                    match
                )

    return found


def extract_focused_event_dates(
    soup: BeautifulSoup,
) -> tuple[list[str], str]:

    selectors = (
        "[datetime]",
        "time",
        ".date",
        ".event-date",
        ".event_date",
        ".eventDate",
        ".start-date",
        ".startDate",
        ".event-details__date",
        ".event-details",
        ".event-info",
        ".event-meta",
    )

    candidates = []

    for selector in selectors:

        try:

            elements = soup.select(
                selector
            )

        except Exception:

            elements = []

        for element in elements:

            value = (
                element.get(
                    "datetime"
                )
                or element.get_text(
                    " ",
                    strip=True,
                )
            )

            if value:

                candidates.append(
                    clean_value(
                        value
                    )
                )

    # Date labels.
    for element in soup.find_all(
        string=re.compile(
            r"\b("
            r"event date|"
            r"start date|"
            r"date|"
            r"when|"
            r"starts"
            r")\b",
            re.IGNORECASE,
        )
    ):

        parent = element.parent

        if not parent:
            continue

        block = clean_value(
            parent.get_text(
                " ",
                strip=True,
            )
        )

        if len(block) <= 500:

            candidates.append(
                block
            )

    parsed = []

    for candidate in candidates:

        for date_text in (
            extract_dates_from_text(
                candidate
            )
        ):

            parsed.extend(
                expand_date_range(
                    date_text
                )
            )

        direct = iso_to_date(
            candidate
        )

        if direct:

            parsed.append(
                direct
            )

    parsed = sorted(
        set(parsed)
    )

    today = today_india()

    # Ignore old unrelated dates where possible.
    relevant = [
        value
        for value in parsed
        if value >= today - timedelta(
            days=1
        )
    ]

    if relevant:

        parsed = relevant

    if len(parsed) > 15:

        parsed = parsed[:15]

    if not parsed:

        return [], ""

    return (
        dates_to_strings(
            parsed
        ),
        "focused HTML/date extraction",
    )


# ============================================================
# INDIAN CITY DETECTION
# ============================================================

def infer_indian_city(
    text: str,
) -> tuple[str, str, str]:

    lowered = text.lower()

    for (
        city,
        state,
        country,
    ) in CITY_STATE_COUNTRY:

        if re.search(
            rf"\b{re.escape(city.lower())}\b",
            lowered,
        ):

            return (
                city,
                state,
                country,
            )

    return "", "", ""


# ============================================================
# LOCATION CLEANING
# ============================================================

def clean_location(
    location: str,
) -> str:

    location = clean_value(
        location
    )

    if not location:
        return ""

    # Remove repeated identical comma-separated components.
    parts = [
        clean_value(part)
        for part in location.split(",")
    ]

    cleaned_parts = []
    seen = set()

    for part in parts:

        if not part:
            continue

        key = part.lower()

        if key in seen:
            continue

        seen.add(key)

        cleaned_parts.append(
            part
        )

    location = ", ".join(
        cleaned_parts
    )

    # Remove obvious duplicate sequences.
    changed = True

    while changed:

        changed = False

        parts = [
            clean_value(part)
            for part in location.split(",")
        ]

        for size in range(
            min(4, len(parts) // 2),
            0,
            -1,
        ):

            first = [
                x.lower()
                for x in parts[:size]
            ]

            second = [
                x.lower()
                for x in parts[
                    size:size * 2
                ]
            ]

            if (
                first
                and first == second
            ):

                parts = parts[size:]

                location = ", ".join(
                    parts
                )

                changed = True
                break

    return clean_value(
        location
    )


# ============================================================
# LOCATION EXTRACTION
# ============================================================

def extract_html_location(
    soup: BeautifulSoup,
) -> tuple[
    str,
    str,
    str,
    str,
    str,
]:

    selectors = (
        "[itemprop='location']",
        "[itemprop='address']",
        ".location",
        ".event-location",
        ".event_location",
        ".venue",
        ".event-venue",
        ".address",
        ".event-address",
    )

    candidates = []

    for selector in selectors:

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

            if not text:
                continue

            if len(text) > 500:
                continue

            candidates.append(
                text
            )

    candidates = (
        dedupe_preserve_order(
            candidates
        )
    )

    if not candidates:

        return (
            "",
            "",
            "",
            "",
            "",
        )

    # Prefer the shortest meaningful location.
    candidates.sort(
        key=lambda x: (
            len(x),
            x.lower().count(","),
        )
    )

    location = clean_location(
        candidates[0]
    )

    city, state, country = (
        infer_indian_city(
            location
        )
    )

    return (
        location,
        city,
        state,
        country,
        "HTML location element",
    )


# ============================================================
# VENUE
# ============================================================

def extract_html_venue(
    soup: BeautifulSoup,
) -> str:

    selectors = (
        "[itemprop='location'] [itemprop='name']",
        ".venue-name",
        ".event-venue",
        ".venue",
        "[class*='venue-name']",
    )

    candidates = []

    for selector in selectors:

        try:

            elements = soup.select(
                selector
            )

        except Exception:

            elements = []

        for element in elements[:10]:

            text = clean_value(
                element.get_text(
                    " ",
                    strip=True,
                )
            )

            if not text:
                continue

            if len(text) > 150:
                continue

            candidates.append(
                text
            )

    for candidate in (
        dedupe_preserve_order(
            candidates
        )
    ):

        if candidate.lower() in (
            "location",
            "venue",
            "address",
        ):
            continue

        return candidate

    return ""


# ============================================================
# TIME
# ============================================================

def extract_time(
    text: str,
) -> str:

    patterns = (
        r"\b\d{1,2}:\d{2}\s*"
        r"(?:AM|PM)"
        r"\s*[-–—]\s*"
        r"\d{1,2}:\d{2}\s*"
        r"(?:AM|PM)\b",

        r"\b\d{1,2}\s*"
        r"(?:AM|PM)"
        r"\s*[-–—]\s*"
        r"\d{1,2}\s*"
        r"(?:AM|PM)\b",

        r"\b\d{1,2}:\d{2}\s*"
        r"(?:AM|PM)\b",

        r"\b\d{1,2}\s*"
        r"(?:AM|PM)\b",
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
# ORGANIZER
# ============================================================

def extract_organizer(
    soup: BeautifulSoup,
) -> str:

    selectors = (
        "[itemprop='organizer']",
        ".organizer",
        ".event-organizer",
        ".event_organizer",
        "[class*='organizer']",
    )

    for selector in selectors:

        try:

            elements = soup.select(
                selector
            )

        except Exception:

            elements = []

        for element in elements[:10]:

            text = clean_value(
                element.get_text(
                    " ",
                    strip=True,
                )
            )

            if (
                text
                and len(text) <= 150
            ):

                return text

    return ""


# ============================================================
# EVENT TYPE
# ============================================================

def detect_event_type(
    title: str,
    text: str,
) -> str:

    combined = (
        f"{title} {text}"
    ).lower()

    mapping = (
        ("hackathon", "Hackathon"),
        ("bootcamp", "Bootcamp"),
        ("workshop", "Workshop"),
        ("webinar", "Webinar"),
        ("conference", "Conference"),
        ("summit", "Summit"),
        ("meetup", "Meetup"),
        ("training", "Training"),
        ("seminar", "Seminar"),
        ("symposium", "Symposium"),
        ("masterclass", "Masterclass"),
        ("competition", "Competition"),
        ("challenge", "Challenge"),
        ("forum", "Forum"),
        ("expo", "Expo"),
        ("session", "Session"),
        ("talk", "Talk"),
    )

    for keyword, label in mapping:

        if keyword in combined:

            return label

    return ""


# ============================================================
# EVENT MODE
# ============================================================

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
            "physical event",
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

    if re.search(
        r"\bfree\b",
        text,
        flags=re.IGNORECASE,
    ):

        return "Free"

    patterns = (
        r"(?:₹|Rs\.?|INR)\s*"
        r"[\d,]+(?:\.\d{1,2})?",

        r"\$\s*"
        r"[\d,]+(?:\.\d{1,2})?",

        r"€\s*"
        r"[\d,]+(?:\.\d{1,2})?",
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
# REGISTRATION
# ============================================================

def extract_registration_url(
    soup: BeautifulSoup,
    base_url: str,
) -> str:

    for link in soup.find_all(
        "a",
        href=True,
    ):

        label = clean_value(
            link.get_text(
                " ",
                strip=True,
            )
        ).lower()

        href = clean_value(
            link.get(
                "href",
                "",
            )
        )

        if not href:
            continue

        if any(
            keyword in label
            for keyword in (
                "register",
                "registration",
                "ticket",
                "tickets",
                "rsvp",
                "sign up",
                "signup",
                "book now",
                "reserve",
                "join",
            )
        ):

            return urljoin(
                base_url,
                href,
            )

    return ""


# ============================================================
# DESCRIPTION
# ============================================================

def clean_description(
    description: str,
) -> str:

    description = clean_value(
        description
    )

    description = re.sub(
        r"[*_~`]+",
        "",
        description,
    )

    description = re.sub(
        r"\b(skip to content|"
        r"skip to main content|"
        r"navigation|menu)\b",
        "",
        description,
        flags=re.IGNORECASE,
    )

    description = clean_value(
        description
    )

    if len(description) > 1000:

        description = (
            description[:997]
            + "..."
        )

    return description


def extract_description(
    soup: BeautifulSoup,
) -> str:

    selectors = (
        "[itemprop='description']",
        "meta[name='description']",
        "meta[property='og:description']",
        ".event-description",
        ".event_description",
        ".description",
        "article",
    )

    candidates = []

    for selector in selectors:

        try:

            elements = soup.select(
                selector
            )

        except Exception:

            elements = []

        for element in elements[:10]:

            if element.name == "meta":

                text = clean_value(
                    element.get(
                        "content",
                        "",
                    )
                )

            else:

                text = clean_value(
                    element.get_text(
                        " ",
                        strip=True,
                    )
                )

            if (
                text
                and len(text) >= 40
            ):

                candidates.append(
                    text
                )

    candidates = (
        dedupe_preserve_order(
            candidates
        )
    )

    if not candidates:

        return ""

    return clean_description(
        candidates[0]
    )


# ============================================================
# CYBERSECURITY VALIDATION
# ============================================================

def cybersecurity_relevance(
    title: str,
    description: str,
    text: str,
) -> tuple[bool, int]:

    title_hits = keyword_count(
        title,
        CYBER_KEYWORDS,
    )

    description_hits = keyword_count(
        description,
        CYBER_KEYWORDS,
    )

    full_hits = keyword_count(
        text,
        CYBER_KEYWORDS,
    )

    # Strongest signal:
    # cybersecurity term in title.
    if title_hits > 0:

        return (
            True,
            min(
                100,
                70 + title_hits * 10,
            ),
        )

    # Cybersecurity mentioned in actual description.
    if description_hits > 0:

        return (
            True,
            min(
                100,
                60 + description_hits * 10,
            ),
        )

    # Multiple cyber signals throughout page.
    if full_hits >= 2:

        return (
            True,
            min(
                100,
                50 + full_hits * 5,
            ),
        )

    return False, 0


# ============================================================
# EVENT VALIDATION
# ============================================================

def event_relevance(
    title: str,
    text: str,
) -> bool:

    title_lower = title.lower()

    # Strong event indicators.
    if contains_keyword(
        title,
        EVENT_KEYWORDS,
    ):

        return True

    # If the title is weak, look for event terms
    # in the page.
    return contains_keyword(
        text,
        EVENT_KEYWORDS,
    )


# ============================================================
# INDIA / INTERNATIONAL ONLINE VALIDATION
# ============================================================

def detect_india_location(
    location_text: str,
    page_text: str,
    event_mode: str,
) -> tuple[
    bool,
    str,
    str,
    str,
    str,
]:

    location_lower = (
        location_text.lower()
    )

    mode_lower = (
        event_mode.lower()
    )

    # --------------------------------------------------------
    # ONLINE / REMOTE / VIRTUAL
    # --------------------------------------------------------
    #
    # IMPORTANT:
    #
    # International online cybersecurity events
    # are allowed.
    #
    # Example:
    # USA online cybersecurity event -> ALLOW
    # UK remote AppSec webinar -> ALLOW
    # Singapore virtual security summit -> ALLOW
    #
    # India is NOT required for online events.
    # --------------------------------------------------------

    is_remote = (
        "online" in mode_lower
        or "remote" in mode_lower
        or "virtual" in mode_lower
        or contains_keyword(
            location_text,
            ONLINE_KEYWORDS,
        )
        or contains_keyword(
            page_text,
            ONLINE_KEYWORDS,
        )
    )

    if is_remote:

        city, state, country = (
            infer_indian_city(
                location_text
            )
        )

        if city:

            return (
                True,
                city,
                state,
                country,
                "Online/remote event with Indian location",
            )

        return (
            True,
            "",
            "",
            "",
            "Online/remote event - international events allowed",
        )

    # --------------------------------------------------------
    # PHYSICAL EVENTS
    # --------------------------------------------------------
    #
    # Physical events MUST be in India.
    # --------------------------------------------------------

    city, state, country = (
        infer_indian_city(
            location_text
        )
    )

    if city:

        return (
            True,
            city,
            state,
            country,
            "Indian city detected in event location",
        )

    if re.search(
        r"\bindia\b",
        location_lower,
        flags=re.IGNORECASE,
    ):

        return (
            True,
            "",
            "",
            "India",
            "India detected in event location",
        )

    # Explicit foreign physical location.
    for country_name in (
        NON_INDIA_COUNTRIES
    ):

        if country_name in location_lower:

            return (
                False,
                "",
                "",
                "",
                (
                    "Physical event outside India: "
                    f"{country_name}"
                ),
            )

    return (
        False,
        "",
        "",
        "",
        "Physical event location is not in India",
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

    # --------------------------------------------------------
    # DOWNLOAD PAGE
    # --------------------------------------------------------

    try:

        response = requests.get(
            url,
            timeout=TIMEOUT,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": (
                    "en-US,en;q=0.9"
                ),
            },
            allow_redirects=True,
        )

        response.raise_for_status()

        result.reachable = True

    except requests.RequestException as exc:

        result.reachable = False

        result.rejected_reason = (
            f"Page unreachable: {exc}"
        )

        return result

    # --------------------------------------------------------
    # PARSE HTML
    # --------------------------------------------------------

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    # --------------------------------------------------------
    # JSON-LD MUST BE READ BEFORE SCRIPT REMOVAL
    # --------------------------------------------------------

    structured_events = (
        extract_jsonld_events(
            soup
        )
    )

    structured_event = (
        extract_structured_event(
            structured_events
        )
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = ""

    # OpenGraph title.
    og_title = soup.find(
        "meta",
        attrs={
            "property": "og:title"
        },
    )

    if og_title:

        title = clean_title(
            og_title.get(
                "content",
                "",
            )
        )

    # HTML title.
    if not title:

        title_tag = soup.find(
            "title"
        )

        if title_tag:

            title = clean_title(
                title_tag.get_text(
                    " ",
                    strip=True,
                )
            )

    # JSON-LD title has priority.
    if structured_event:

        structured_title = (
            clean_title(
                structured_event.get(
                    "name",
                    "",
                )
            )
        )

        if structured_title:

            title = (
                structured_title
            )

    result.title = title

    # --------------------------------------------------------
    # APPLY STRUCTURED EVENT
    # --------------------------------------------------------

    if structured_event:

        apply_structured_event(
            result,
            structured_event,
            response.url,
        )

    # --------------------------------------------------------
    # REMOVE NON-CONTENT ELEMENTS
    # --------------------------------------------------------

    for element in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "nav",
            "footer",
            "header",
        ]
    ):

        element.decompose()

    # --------------------------------------------------------
    # CLEAN PAGE TEXT
    # --------------------------------------------------------

    page_text = normalize_text(
        soup.get_text(
            " ",
            strip=True,
        )
    )

    result.text = page_text

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    if not result.event_description:

        result.event_description = (
            extract_description(
                soup
            )
        )

    # --------------------------------------------------------
    # CYBERSECURITY CHECK
    # --------------------------------------------------------

    (
        cyber_ok,
        cyber_strength,
    ) = cybersecurity_relevance(
        result.title,
        result.event_description,
        page_text,
    )

    result.is_cyber_event = (
        cyber_ok
    )

    result.has_cyber_signal = (
        cyber_ok
    )

    # --------------------------------------------------------
    # EVENT CHECK
    # --------------------------------------------------------

    result.is_event_page = (
        event_relevance(
            result.title,
            page_text,
        )
    )

    result.has_event_signal = (
        result.is_event_page
    )

    # --------------------------------------------------------
    # DATE CHECK
    # --------------------------------------------------------

    if not result.detected_dates:

        (
            dates,
            date_source,
        ) = extract_focused_event_dates(
            soup
        )

        if dates:

            result.detected_dates = (
                dates
            )

            result.date_source = (
                date_source
            )

            result.has_date_signal = True

            (
                result.event_date,
                result.event_end_date,
            ) = format_event_dates(
                dates
            )

    result.has_future_date = (
        has_future_date(
            result.detected_dates
        )
    )

    # --------------------------------------------------------
    # LOCATION CHECK
    # --------------------------------------------------------

    if not result.event_location:

        (
            location,
            city,
            state,
            country,
            location_source,
        ) = extract_html_location(
            soup
        )

        result.event_location = (
            clean_location(
                location
            )
        )

        result.event_city = city
        result.event_state = state
        result.event_country = country

        result.location_source = (
            location_source
        )

    else:

        result.event_location = (
            clean_location(
                result.event_location
            )
        )

    # --------------------------------------------------------
    # VENUE
    # --------------------------------------------------------

    if not result.event_venue:

        result.event_venue = (
            extract_html_venue(
                soup
            )
        )

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    if not result.event_time:

        result.event_time = (
            extract_time(
                page_text
            )
        )

    # --------------------------------------------------------
    # ORGANIZER
    # --------------------------------------------------------

    if not result.event_organizer:

        result.event_organizer = (
            extract_organizer(
                soup
            )
        )

    # --------------------------------------------------------
    # EVENT TYPE
    # --------------------------------------------------------

    if not result.event_type:

        result.event_type = (
            detect_event_type(
                result.title,
                page_text,
            )
        )

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    if not result.event_price:

        result.event_price = (
            extract_price(
                page_text
            )
        )

    # --------------------------------------------------------
    # EVENT MODE
    # --------------------------------------------------------

    mode_text = (
        f"{result.event_location} "
        f"{result.event_type} "
        f"{page_text}"
    )

    result.event_mode = (
        detect_event_mode(
            mode_text
        )
    )

    result.has_online_signal = (
        result.event_mode
        in (
            "Online",
            "Hybrid",
        )
    )

    # --------------------------------------------------------
    # REGISTRATION
    # --------------------------------------------------------

    result.registration_url = (
        extract_registration_url(
            soup,
            response.url,
        )
    )

    result.has_registration_signal = (
        bool(
            result.registration_url
        )
        or contains_keyword(
            page_text,
            REGISTRATION_KEYWORDS,
        )
    )

    # --------------------------------------------------------
    # INDIA / INTERNATIONAL ONLINE RULE
    # --------------------------------------------------------

    (
        india_ok,
        india_city,
        india_state,
        india_country,
        india_reason,
    ) = detect_india_location(
        result.event_location,
        page_text,
        result.event_mode,
    )

    # Structured Indian city has priority.
    if result.event_city:

        structured_city, structured_state, structured_country = (
            infer_indian_city(
                result.event_city
            )
        )

        if structured_city:

            india_ok = True

            india_city = (
                structured_city
            )

            india_state = (
                structured_state
            )

            india_country = (
                structured_country
            )

    result.is_india_event = (
        india_ok
    )

    result.has_india_location = (
        india_ok
    )

    if india_ok:

        if not result.event_city:

            result.event_city = (
                india_city
            )

        if not result.event_state:

            result.event_state = (
                india_state
            )

        if not result.event_country:

            result.event_country = (
                india_country
            )

    result.has_location_signal = bool(
        result.event_location
    )

    # --------------------------------------------------------
    # FINAL HARD VALIDATION
    # --------------------------------------------------------
    #
    # ALL cybersecurity events:
    #
    # 1. Must actually be an event.
    # 2. Must actually be cybersecurity-related.
    # 3. Must have a verified current/future date.
    # 4. Physical events must be in India.
    # 5. Online/remote events can be international.
    # --------------------------------------------------------

    if not result.is_event_page:

        result.rejected_reason = (
            "Not a recognizable event page"
        )

    elif not result.is_cyber_event:

        result.rejected_reason = (
            "Cybersecurity relevance not established"
        )

    elif not result.has_date_signal:

        result.rejected_reason = (
            "Event date could not be verified"
        )

    elif not result.has_future_date:

        result.rejected_reason = (
            "Event date is in the past"
        )

    elif not result.is_india_event:

        result.rejected_reason = (
            f"Physical event outside India: "
            f"{india_reason}"
        )

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = 0

    if result.reachable:
        score += 5

    if result.is_event_page:
        score += 15

    if result.is_cyber_event:
        score += 25

    if result.has_date_signal:
        score += 10

    if result.has_future_date:
        score += 15

    if result.is_india_event:
        score += 20

    if result.has_location_signal:
        score += 5

    if result.has_registration_signal:
        score += 5

    result.score = min(
        score,
        100,
    )

    # --------------------------------------------------------
    # HARD REJECTION CAPS SCORE
    # --------------------------------------------------------

    if (
        not result.is_event_page
        or not result.is_cyber_event
        or not result.has_date_signal
        or not result.has_future_date
        or not result.is_india_event
    ):

        result.score = min(
            result.score,
            35,
        )

    return result


# ============================================================
# TODAY EVENT CHECK
# ============================================================

def is_today_event(
    result: VerificationResult,
) -> bool:

    if not result:
        return False

    if not result.is_event_page:
        return False

    if not result.is_cyber_event:
        return False

    if not result.is_india_event:
        return False

    if not result.has_date_signal:
        return False

    return event_is_today(
        result.detected_dates
    )


# ============================================================
# COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:

        print(
            "Usage: "
            "python verifier.py <event_url>"
        )

        raise SystemExit(1)

    test_url = sys.argv[1]

    result = verify_event(
        test_url
    )

    print()
    print("=" * 70)
    print("INDIA CYBERSECURITY EVENT VERIFICATION")
    print("=" * 70)

    print(
        f"Reachable       : "
        f"{result.reachable}"
    )

    print(
        f"Title           : "
        f"{result.title}"
    )

    print(
        f"Event Page      : "
        f"{result.is_event_page}"
    )

    print(
        f"Cybersecurity   : "
        f"{result.is_cyber_event}"
    )

    print(
        f"India/Allowed   : "
        f"{result.is_india_event}"
    )

    print(
        f"Date            : "
        f"{result.event_date}"
    )

    print(
        f"End Date        : "
        f"{result.event_end_date}"
    )

    print(
        f"Time            : "
        f"{result.event_time}"
    )

    print(
        f"Location        : "
        f"{result.event_location}"
    )

    print(
        f"Venue           : "
        f"{result.event_venue}"
    )

    print(
        f"City            : "
        f"{result.event_city}"
    )

    print(
        f"State           : "
        f"{result.event_state}"
    )

    print(
        f"Country         : "
        f"{result.event_country}"
    )

    print(
        f"Mode            : "
        f"{result.event_mode}"
    )

    print(
        f"Organizer       : "
        f"{result.event_organizer}"
    )

    print(
        f"Type            : "
        f"{result.event_type}"
    )

    print(
        f"Price           : "
        f"{result.event_price}"
    )

    print(
        f"Registration    : "
        f"{result.registration_url}"
    )

    print(
        f"Structured      : "
        f"{result.structured_event_found}"
    )

    print(
        f"Score           : "
        f"{result.score}/100"
    )

    print(
        f"Rejected Reason : "
        f"{result.rejected_reason}"
    )

    print("=" * 70)
