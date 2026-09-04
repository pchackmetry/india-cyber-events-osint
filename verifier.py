from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

REQUEST_TIMEOUT = 20

CYBER_KEYWORDS = {
    "cybersecurity",
    "cyber security",
    "information security",
    "infosec",
    "application security",
    "appsec",
    "cloud security",
    "network security",
    "security operations",
    "soc",
    "incident response",
    "threat intelligence",
    "digital forensics",
    "forensics",
    "penetration testing",
    "pentesting",
    "ethical hacking",
    "vulnerability",
    "vulnerabilities",
    "vapt",
    "red team",
    "blue team",
    "purple team",
    "zero trust",
    "identity and access management",
    "iam",
    "devsecops",
    "security engineering",
    "security architecture",
    "security conference",
    "security summit",
    "security webinar",
    "data security",
    "privacy",
    "owasp",
    "ciso",
    "ransomware",
    "malware",
    "threat hunting",
    "secure coding",
    "software security",
    "application security",
}

EVENT_KEYWORDS = {
    "event",
    "conference",
    "summit",
    "webinar",
    "workshop",
    "meetup",
    "seminar",
    "symposium",
    "bootcamp",
    "training",
    "hackathon",
    "expo",
    "forum",
    "roundtable",
    "masterclass",
    "congress",
    "conclave",
    "competition",
}

INDIA_KEYWORDS = {
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
    "lucknow",
    "chandigarh",
    "indore",
    "bhubaneswar",
    "visakhapatnam",
    "vijayawada",
    "thiruvananthapuram",
    "telangana",
    "karnataka",
    "tamil nadu",
    "maharashtra",
    "kerala",
    "andhra pradesh",
    "uttar pradesh",
    "west bengal",
    "rajasthan",
    "gujarat",
    "odisha",
    "haryana",
    "punjab",
    "delhi ncr",
}

NON_INDIA_COUNTRIES = {
    "united states",
    "united states of america",
    "usa",
    "us",
    "u.s.",
    "canada",
    "united kingdom",
    "uk",
    "u.k.",
    "australia",
    "new zealand",
    "germany",
    "france",
    "spain",
    "italy",
    "singapore",
    "japan",
    "china",
    "south korea",
    "korea",
    "ireland",
    "netherlands",
    "switzerland",
    "sweden",
    "norway",
    "denmark",
    "finland",
    "belgium",
    "israel",
    "uae",
    "united arab emirates",
    "dubai",
    "qatar",
    "saudi arabia",
}

ONLINE_KEYWORDS = {
    "online",
    "virtual",
    "webinar",
    "remote",
    "online event",
    "virtual event",
    "online conference",
    "virtual conference",
    "online webinar",
}

HYBRID_KEYWORDS = {
    "hybrid",
    "online and in-person",
    "online & in-person",
    "virtual and in-person",
    "virtual & in-person",
}

LISTING_PAGE_KEYWORDS = {
    "all events",
    "upcoming events",
    "events calendar",
    "event calendar",
    "events listing",
    "event listings",
    "browse events",
    "find events",
    "search events",
    "global events",
    "regional events",
    "events directory",
    "event directory",
    "events page",
    "events archive",
    "event archive",
    "all upcoming events",
    "view all events",
    "see all events",
    "past events",
    "previous events",
    "event categories",
    "events by category",
}

PRICE_FALSE_POSITIVES = {
    "rs",
    "inr",
    "usd",
    "eur",
    "gbp",
    "$",
    "₹",
    "€",
    "£",
}


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass
class VerificationResult:
    reachable: bool = False

    title: str = ""
    text: str = ""

    has_registration_signal: bool = False
    has_date_signal: bool = False
    has_future_date: bool = False
    has_location_signal: bool = False
    has_india_location: bool = False
    has_online_signal: bool = False
    has_cyber_signal: bool = False
    has_event_signal: bool = False

    is_india_event: bool = False
    is_cyber_event: bool = False
    is_event_page: bool = False

    rejected_reason: str = ""

    detected_dates: list[str] = field(default_factory=list)

    event_date: str = ""
    event_end_date: str = ""
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

    registration_url: str = ""
    event_url: str = ""

    event_description: str = ""

    date_source: str = ""
    location_source: str = ""

    structured_event_found: bool = False

    score: int = 0


# ============================================================
# BASIC HELPERS
# ============================================================

def normalize_space(value: Any) -> str:
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def clean_text(value: Any) -> str:
    value = normalize_space(value)

    if value.lower() in {
        "none",
        "null",
        "n/a",
        "na",
        "not available",
        "not specified",
        "not found",
    }:
        return ""

    return value


def contains_keyword(text: str, keywords: set[str]) -> bool:
    text = text.lower()

    return any(keyword in text for keyword in keywords)


def safe_get(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)

        if value not in (None, "", [], {}):
            return value

    return ""


def absolute_url(base_url: str, value: Any) -> str:
    value = clean_text(value)

    if not value:
        return ""

    return urljoin(base_url, value)


def valid_url(value: str) -> bool:
    return bool(
        re.match(
            r"^https?://",
            value or "",
            flags=re.IGNORECASE,
        )
    )


# ============================================================
# HTML FETCHING
# ============================================================

def fetch_page(url: str) -> tuple[bool, str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; "
            "India-Cybersecurity-OSINT-Scanner/1.0)"
        )
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()

        return (
            True,
            response.url,
            response.text,
        )

    except requests.RequestException:
        return False, url, ""


# ============================================================
# JSON-LD
# ============================================================

def flatten_jsonld(value: Any) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    if isinstance(value, dict):
        if "@graph" in value:
            output.extend(flatten_jsonld(value["@graph"]))

        if "@type" in value:
            output.append(value)

        for item in value.values():
            if isinstance(item, (dict, list)):
                output.extend(flatten_jsonld(item))

    elif isinstance(value, list):
        for item in value:
            output.extend(flatten_jsonld(item))

    return output


def extract_jsonld(soup: BeautifulSoup) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []

    for script in soup.find_all(
        "script",
        attrs={"type": "application/ld+json"},
    ):
        raw = script.string or script.get_text()

        if not raw:
            continue

        try:
            data = json.loads(raw)
            objects.extend(flatten_jsonld(data))

        except (json.JSONDecodeError, TypeError):
            continue

    return objects


def is_event_type(value: Any) -> bool:
    if isinstance(value, list):
        return any(is_event_type(item) for item in value)

    value = clean_text(value).lower()

    return value == "event" or value.endswith("event")


def find_structured_event(
    objects: list[dict[str, Any]],
) -> dict[str, Any]:
    for obj in objects:
        if is_event_type(obj.get("@type")):
            return obj

    return {}


# ============================================================
# DATE EXTRACTION
# ============================================================

MONTHS = (
    "January|February|March|April|May|June|July|August|"
    "September|October|November|December"
)

MONTH_PATTERN = re.compile(
    rf"\b(?:{MONTHS})\s+\d{{1,2}}(?:,\s*\d{{4}})?\b",
    re.IGNORECASE,
)

NUMERIC_DATE_PATTERN = re.compile(
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
)


def parse_date_string(value: Any) -> str:
    value = clean_text(value)

    if not value:
        return ""

    value = value.replace("T", " ")

    iso_match = re.search(
        r"\b(\d{4})-(\d{2})-(\d{2})\b",
        value,
    )

    if iso_match:
        try:
            dt = date(
                int(iso_match.group(1)),
                int(iso_match.group(2)),
                int(iso_match.group(3)),
            )

            return dt.strftime("%d %B %Y")

        except ValueError:
            pass

    month_match = re.search(
        rf"\b({MONTHS})\s+(\d{{1,2}})(?:,\s*(\d{{4}}))?\b",
        value,
        flags=re.IGNORECASE,
    )

    if month_match and month_match.group(3):
        try:
            dt = datetime.strptime(
                f"{month_match.group(1)} "
                f"{month_match.group(2)} "
                f"{month_match.group(3)}",
                "%B %d %Y",
            ).date()

            return dt.strftime("%d %B %Y")

        except ValueError:
            pass

    numeric_match = NUMERIC_DATE_PATTERN.search(value)

    if numeric_match:
        raw = numeric_match.group(0)

        for fmt in (
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%d/%m/%y",
            "%m/%d/%y",
        ):
            try:
                dt = datetime.strptime(raw, fmt).date()

                return dt.strftime("%d %B %Y")

            except ValueError:
                continue

    return ""


def parse_iso_date(value: Any) -> date | None:
    value = clean_text(value)

    if not value:
        return None

    match = re.search(
        r"(\d{4})-(\d{2})-(\d{2})",
        value,
    )

    if not match:
        return None

    try:
        return date(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
        )

    except ValueError:
        return None


def extract_dates_from_text(text: str) -> list[str]:
    results: list[str] = []

    for match in MONTH_PATTERN.finditer(text):
        parsed = parse_date_string(match.group(0))

        if parsed and parsed not in results:
            results.append(parsed)

    for match in NUMERIC_DATE_PATTERN.finditer(text):
        parsed = parse_date_string(match.group(0))

        if parsed and parsed not in results:
            results.append(parsed)

    return results


def date_is_current_or_future(date_text: str) -> bool:
    parsed = parse_date_string(date_text)

    if not parsed:
        return False

    try:
        event_dt = datetime.strptime(
            parsed,
            "%d %B %Y",
        ).date()

        return event_dt >= date.today()

    except ValueError:
        return False


def extract_structured_dates(
    event: dict[str, Any],
) -> tuple[str, str]:
    start_raw = safe_get(
        event,
        "startDate",
        "startTime",
        "start",
    )

    end_raw = safe_get(
        event,
        "endDate",
        "endTime",
        "end",
    )

    start_date = parse_date_string(start_raw)
    end_date = parse_date_string(end_raw)

    return start_date, end_date


# ============================================================
# LOCATION
# ============================================================

def structured_location(
    event: dict[str, Any],
) -> tuple[str, str, str, str, str]:
    location = event.get("location")

    if isinstance(location, list):
        location = location[0] if location else {}

    if isinstance(location, str):
        return (
            clean_text(location),
            "",
            "",
            "",
            "",
        )

    if not isinstance(location, dict):
        return "", "", "", "", ""

    address = location.get("address", {})

    if isinstance(address, str):
        return (
            clean_text(address),
            "",
            "",
            "",
            "",
        )

    if not isinstance(address, dict):
        address = {}

    name = clean_text(
        safe_get(
            location,
            "name",
            "venue",
        )
    )

    city = clean_text(
        safe_get(
            address,
            "addressLocality",
            "city",
        )
    )

    state = clean_text(
        safe_get(
            address,
            "addressRegion",
            "state",
        )
    )

    country = clean_text(
        safe_get(
            address,
            "addressCountry",
            "country",
        )
    )

    street = clean_text(
        safe_get(
            address,
            "streetAddress",
            "addressLine1",
        )
    )

    parts = [
        name,
        street,
        city,
        state,
        country,
    ]

    location_text = ", ".join(
        item for item in parts if item
    )

    return (
        location_text,
        name,
        city,
        state,
        country,
    )


def extract_location_from_text(
    text: str,
) -> tuple[str, str, str]:
    online = contains_keyword(
        text,
        ONLINE_KEYWORDS,
    )

    if online:
        return (
            "Online / Virtual",
            "",
            "",
        )

    patterns = [
        r"(?:location|venue|where)\s*[:\-]\s*([^|.\n]{3,160})",
        r"(?:held at|taking place at)\s+([^|.\n]{3,160})",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        value = normalize_space(match.group(1))

        if len(value) > 160:
            continue

        return (
            value,
            "",
            "",
        )

    return "", "", ""


# ============================================================
# EVENT MODE
# ============================================================

def detect_event_mode(
    text: str,
    location: str,
) -> str:
    combined = f"{text} {location}".lower()

    if contains_keyword(
        combined,
        HYBRID_KEYWORDS,
    ):
        return "Hybrid"

    if contains_keyword(
        combined,
        ONLINE_KEYWORDS,
    ):
        return "Online"

    return "Offline"


# ============================================================
# COUNTRY / INDIA VALIDATION
# ============================================================

def detect_foreign_location(
    text: str,
) -> str:
    lowered = text.lower()

    for country in sorted(
        NON_INDIA_COUNTRIES,
        key=len,
        reverse=True,
    ):
        pattern = r"(?<![a-z])" + re.escape(country) + r"(?![a-z])"

        if re.search(pattern, lowered):
            return country

    return ""


def detect_india_location(
    location_text: str,
    page_text: str,
    event_mode: str,
) -> bool:
    location_lower = location_text.lower()
    page_lower = page_text.lower()

    if event_mode == "Online":
        return True

    if event_mode == "Hybrid":
        return contains_keyword(
            location_lower,
            INDIA_KEYWORDS,
        )

    foreign = detect_foreign_location(
        location_lower,
    )

    if foreign:
        return False

    return contains_keyword(
        location_lower,
        INDIA_KEYWORDS,
    )


# ============================================================
# TIME
# ============================================================

def extract_time(
    event: dict[str, Any],
    text: str,
) -> str:
    structured = clean_text(
        safe_get(
            event,
            "startDate",
            "startTime",
        )
    )

    if structured:
        match = re.search(
            r"T(\d{2}:\d{2})(?::\d{2})?",
            structured,
        )

        if match:
            return match.group(1)

    patterns = [
        r"\b\d{1,2}:\d{2}\s*(?:AM|PM)\b",
        r"\b\d{1,2}\s*(?:AM|PM)\b",
        r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return normalize_space(
                match.group(0)
            )

    return ""


# ============================================================
# ORGANIZER
# ============================================================

def extract_organizer(
    event: dict[str, Any],
    text: str,
) -> str:
    organizer = event.get("organizer")

    if isinstance(organizer, list):
        organizer = (
            organizer[0]
            if organizer
            else {}
        )

    if isinstance(organizer, dict):
        value = clean_text(
            safe_get(
                organizer,
                "name",
                "legalName",
            )
        )

        if value:
            return value

    if isinstance(organizer, str):
        value = clean_text(organizer)

        if value:
            return value

    patterns = [
        r"organizer\s*[:\-]\s*([^|.\n]{2,100})",
        r"organised by\s+([^|.\n]{2,100})",
        r"organized by\s+([^|.\n]{2,100})",
        r"hosted by\s+([^|.\n]{2,100})",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return normalize_space(
                match.group(1)
            )

    return ""


# ============================================================
# EVENT TYPE
# ============================================================

def extract_event_type(
    event: dict[str, Any],
    text: str,
) -> str:
    value = clean_text(
        safe_get(
            event,
            "eventType",
            "type",
        )
    )

    if value and value.lower() != "event":
        return value

    lowered = text.lower()

    for event_type in (
        "webinar",
        "conference",
        "summit",
        "workshop",
        "meetup",
        "seminar",
        "symposium",
        "hackathon",
        "training",
        "bootcamp",
        "expo",
        "forum",
        "roundtable",
        "masterclass",
        "congress",
        "conclave",
    ):
        if event_type in lowered:
            return event_type.title()

    return "Event"


# ============================================================
# PRICE
# ============================================================

def extract_price(
    event: dict[str, Any],
    text: str,
) -> str:
    offers = event.get("offers")

    if isinstance(offers, list):
        offers = offers[0] if offers else {}

    if isinstance(offers, dict):
        price = clean_text(
            safe_get(
                offers,
                "price",
                "lowPrice",
            )
        )

        currency = clean_text(
            safe_get(
                offers,
                "priceCurrency",
                "currency",
            )
        )

        if price and re.search(
            r"\d",
            price,
        ):
            return (
                f"{currency} {price}".strip()
                if currency
                else price
            )

    patterns = [
        r"(?:₹|INR|Rs\.?|USD|\$|EUR|€|GBP|£)\s*[\d,]+(?:\.\d{1,2})?",
        r"[\d,]+(?:\.\d{1,2})?\s*(?:INR|USD|EUR|GBP)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            value = normalize_space(
                match.group(0)
            )

            if value.lower().strip() in PRICE_FALSE_POSITIVES:
                continue

            if not re.search(
                r"\d",
                value,
            ):
                continue

            return value

    if re.search(
        r"\bfree(?: registration| event)?\b",
        text,
        flags=re.IGNORECASE,
    ):
        return "Free"

    return "Not specified"


# ============================================================
# REGISTRATION
# ============================================================

def extract_registration_url(
    soup: BeautifulSoup,
    base_url: str,
) -> str:
    registration_words = (
        "register",
        "registration",
        "tickets",
        "rsvp",
        "sign up",
        "book now",
        "attend",
        "join event",
    )

    for link in soup.find_all("a", href=True):
        label = normalize_space(
            link.get_text(" ", strip=True)
        ).lower()

        href = absolute_url(
            base_url,
            link.get("href"),
        )

        if not valid_url(href):
            continue

        if any(
            word in label
            for word in registration_words
        ):
            return href

    return ""


# ============================================================
# DESCRIPTION
# ============================================================

def extract_description(
    event: dict[str, Any],
    soup: BeautifulSoup,
    text: str,
) -> str:
    value = clean_text(
        safe_get(
            event,
            "description",
        )
    )

    if value:
        return value[:1000]

    meta = soup.find(
        "meta",
        attrs={"name": "description"},
    )

    if meta:
        value = clean_text(
            meta.get("content"),
        )

        if value:
            return value[:1000]

    return text[:1000]


# ============================================================
# LISTING PAGE DETECTION
# ============================================================

def is_probable_listing_page(
    title: str,
    text: str,
    event: dict[str, Any],
    dates: list[str],
) -> bool:
    title_lower = title.lower().strip()

    if any(
        phrase in title_lower
        for phrase in LISTING_PAGE_KEYWORDS
    ):
        return True

    if not event:
        return False

    event_name = clean_text(
        event.get("name")
    ).lower()

    if not event_name:
        return False

    page_lower = text.lower()

    listing_signal_count = sum(
        1
        for phrase in LISTING_PAGE_KEYWORDS
        if phrase in page_lower
    )

    # A page with many unrelated dates is normally an
    # index/calendar rather than one individual event.
    if len(dates) >= 8:
        return True

    if listing_signal_count >= 3:
        return True

    # Generic "Global Events" / "Regional Events" names
    # are category/index pages unless they have a concrete
    # event start date.
    generic_names = {
        "global events",
        "regional events",
        "all events",
        "upcoming events",
        "events",
        "events calendar",
        "event calendar",
    }

    if event_name in generic_names:
        start_date = clean_text(
            safe_get(
                event,
                "startDate",
                "startTime",
            )
        )

        if not start_date:
            return True

    return False


# ============================================================
# CYBERSECURITY VALIDATION
# ============================================================

def cybersecurity_relevance(
    title: str,
    description: str,
    text: str,
) -> bool:
    combined = (
        f"{title} "
        f"{description} "
        f"{text}"
    ).lower()

    return contains_keyword(
        combined,
        CYBER_KEYWORDS,
    )


def event_relevance(
    title: str,
    description: str,
    text: str,
) -> bool:
    combined = (
        f"{title} "
        f"{description} "
        f"{text}"
    ).lower()

    return contains_keyword(
        combined,
        EVENT_KEYWORDS,
    )


# ============================================================
# SCORING
# ============================================================

def calculate_score(
    result: VerificationResult,
) -> int:
    score = 0

    if result.reachable:
        score += 10

    if result.structured_event_found:
        score += 25

    if result.has_cyber_signal:
        score += 20

    if result.has_event_signal:
        score += 10

    if result.has_date_signal:
        score += 10

    if result.has_future_date:
        score += 5

    if result.has_registration_signal:
        score += 5

    if result.has_location_signal:
        score += 5

    if result.has_india_location:
        score += 5

    if result.has_online_signal:
        score += 5

    if result.is_cyber_event:
        score += 5

    if result.is_event_page:
        score += 5

    # Strong caps prevent weak/index pages from receiving
    # high confidence.
    if not result.has_cyber_signal:
        score = min(score, 25)

    if not result.has_event_signal:
        score = min(score, 30)

    if not result.has_date_signal:
        score = min(score, 30)

    if (
        result.event_mode != "Online"
        and not result.has_india_location
    ):
        score = min(score, 35)

    if result.rejected_reason:
        score = min(score, 35)

    if is_listing_result(result):
        score = min(score, 20)

    return max(
        0,
        min(100, score),
    )


def is_listing_result(
    result: VerificationResult,
) -> bool:
    reason = (
        result.rejected_reason or ""
    ).lower()

    return (
        "listing" in reason
        or "index" in reason
        or "category" in reason
    )


def verification_score(
    result: VerificationResult,
) -> int:
    """
    Compatibility helper used by pipeline.py.
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
# MAIN VERIFICATION
# ============================================================

def verify_event(
    url: str,
) -> VerificationResult:
    result = VerificationResult(
        event_url=url,
    )

    reachable, final_url, html = fetch_page(url)

    result.reachable = reachable
    result.event_url = final_url

    if not reachable:
        result.rejected_reason = (
            "Page could not be reached"
        )
        result.score = calculate_score(result)
        return result

    soup = BeautifulSoup(
        html,
        "html.parser",
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

    title = normalize_space(
        soup.title.get_text()
        if soup.title
        else ""
    )

    text = normalize_space(
        soup.get_text(
            " ",
            strip=True,
        )
    )

    result.title = title
    result.text = text[:10000]

    jsonld_objects = extract_jsonld(
        BeautifulSoup(
            html,
            "html.parser",
        )
    )

    structured_event = find_structured_event(
        jsonld_objects
    )

    result.structured_event_found = bool(
        structured_event
    )

    # --------------------------------------------------------
    # Structured event information
    # --------------------------------------------------------

    start_date, end_date = (
        extract_structured_dates(
            structured_event
        )
        if structured_event
        else ("", "")
    )

    result.event_date = start_date
    result.event_end_date = end_date

    if start_date:
        result.date_source = "Schema.org"

    structured_location_text = ""
    structured_venue = ""
    structured_city = ""
    structured_state = ""
    structured_country = ""

    if structured_event:
        (
            structured_location_text,
            structured_venue,
            structured_city,
            structured_state,
            structured_country,
        ) = structured_location(
            structured_event
        )

    result.event_location = (
        structured_location_text
    )

    result.event_venue = structured_venue
    result.event_city = structured_city
    result.event_state = structured_state
    result.event_country = structured_country

    result.event_time = extract_time(
        structured_event,
        text,
    )

    result.event_organizer = extract_organizer(
        structured_event,
        text,
    )

    result.event_type = extract_event_type(
        structured_event,
        text,
    )

    result.event_price = extract_price(
        structured_event,
        text,
    )

    result.event_description = extract_description(
        structured_event,
        soup,
        text,
    )

    # --------------------------------------------------------
    # Fallback location
    # --------------------------------------------------------

    if not result.event_location:
        (
            fallback_location,
            fallback_city,
            fallback_state,
        ) = extract_location_from_text(text)

        if fallback_location:
            result.event_location = (
                fallback_location
            )

            result.event_city = fallback_city
            result.event_state = fallback_state
            result.location_source = "Page text"

    if not result.location_source:
        if structured_location_text:
            result.location_source = "Schema.org"

    # --------------------------------------------------------
    # Fallback dates
    # --------------------------------------------------------

    page_dates = extract_dates_from_text(
        text
    )

    if start_date:
        detected_dates = [start_date]

        if end_date and end_date != start_date:
            detected_dates.append(end_date)

    else:
        detected_dates = page_dates[:5]

        if detected_dates:
            result.event_date = (
                detected_dates[0]
            )
            result.date_source = "Page text"

    result.detected_dates = detected_dates

    # --------------------------------------------------------
    # Event mode
    # --------------------------------------------------------

    result.event_mode = detect_event_mode(
        text,
        result.event_location,
    )

    result.has_online_signal = (
        result.event_mode == "Online"
    )

    # --------------------------------------------------------
    # Registration
    # --------------------------------------------------------

    result.registration_url = (
        extract_registration_url(
            BeautifulSoup(
                html,
                "html.parser",
            ),
            final_url,
        )
    )

    result.has_registration_signal = bool(
        result.registration_url
        or re.search(
            r"\b(register|registration|rsvp|tickets|sign up)\b",
            text,
            flags=re.IGNORECASE,
        )
    )

    # --------------------------------------------------------
    # Relevance
    # --------------------------------------------------------

    result.has_cyber_signal = (
        cybersecurity_relevance(
            result.title,
            result.event_description,
            text,
        )
    )

    result.has_event_signal = (
        event_relevance(
            result.title,
            result.event_description,
            text,
        )
    )

    result.is_cyber_event = (
        result.has_cyber_signal
    )

    result.is_event_page = (
        result.has_event_signal
        and result.structured_event_found
    )

    # --------------------------------------------------------
    # Listing/index page detection
    # --------------------------------------------------------

    if is_probable_listing_page(
        result.title,
        text,
        structured_event,
        page_dates,
    ):
        result.rejected_reason = (
            "Event listing/index/category page "
            "rather than a single individual event"
        )

        result.is_event_page = False

    # --------------------------------------------------------
    # Date validation
    # --------------------------------------------------------

    if result.event_date:
        result.has_date_signal = True
        result.has_future_date = (
            date_is_current_or_future(
                result.event_date
            )
        )

    # Do not accept an extracted date from a listing
    # page as a real event date.
    if is_listing_result(result):
        result.event_date = ""
        result.event_end_date = ""
        result.has_date_signal = False
        result.has_future_date = False
        result.detected_dates = []

    # --------------------------------------------------------
    # Location validation
    # --------------------------------------------------------

    result.has_location_signal = bool(
        result.event_location
    )

    result.has_india_location = (
        detect_india_location(
            result.event_location,
            text,
            result.event_mode,
        )
    )

    result.is_india_event = (
        result.has_india_location
    )

    # --------------------------------------------------------
    # Hard rejection rules
    # --------------------------------------------------------

    if not result.has_cyber_signal:
        result.rejected_reason = (
            result.rejected_reason
            or "Not sufficiently cybersecurity related"
        )

    elif not result.has_event_signal:
        result.rejected_reason = (
            result.rejected_reason
            or "Not recognized as an event"
        )

    elif not result.has_date_signal:
        result.rejected_reason = (
            result.rejected_reason
            or "No reliable individual event date found"
        )

    elif not result.has_future_date:
        result.rejected_reason = (
            result.rejected_reason
            or "Event date is in the past"
        )

    elif (
        result.event_mode != "Online"
        and not result.has_india_location
    ):
        foreign = detect_foreign_location(
            result.event_location
        )

        if foreign:
            result.rejected_reason = (
                f"Physical event is outside India "
                f"({foreign})"
            )

        else:
            result.rejected_reason = (
                "Physical/hybrid event location "
                "could not be verified as India"
            )

    # --------------------------------------------------------
    # Additional sanity checks
    # --------------------------------------------------------

    if result.event_price:
        if (
            result.event_price.lower().strip()
            in PRICE_FALSE_POSITIVES
        ):
            result.event_price = "Not specified"

    if (
        result.event_date
        and result.event_end_date
    ):
        start = parse_date_string(
            result.event_date
        )
        end = parse_date_string(
            result.event_end_date
        )

        if start and end:
            try:
                start_dt = datetime.strptime(
                    start,
                    "%d %B %Y",
                ).date()

                end_dt = datetime.strptime(
                    end,
                    "%d %B %Y",
                ).date()

                # Reject absurd multi-year ranges.
                if (
                    end_dt < start_dt
                    or (end_dt - start_dt).days > 31
                ):
                    result.event_end_date = ""

            except ValueError:
                result.event_end_date = ""

    # --------------------------------------------------------
    # Final score
    # --------------------------------------------------------

    result.score = calculate_score(
        result
    )

    return result


# ============================================================
# TODAY HELPER
# ============================================================

def event_is_today(
    result: VerificationResult,
) -> bool:
    if not result.event_date:
        return False

    parsed = parse_date_string(
        result.event_date
    )

    if not parsed:
        return False

    try:
        event_dt = datetime.strptime(
            parsed,
            "%d %B %Y",
        ).date()

        return event_dt == date.today()

    except ValueError:
        return False


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python verifier.py <URL>"
        )
        raise SystemExit(1)

    url = sys.argv[1]

    result = verify_event(url)

    print(
        json.dumps(
            {
                key: value
                for key, value in result.__dict__.items()
            },
            indent=2,
            ensure_ascii=False,
        )
    )
