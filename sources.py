# sources.py

from __future__ import annotations

from typing import Final


# ============================================================
# EVENT SOURCES
# ============================================================

SOURCES: Final[dict[str, dict[str, object]]] = {
    "owasp": {
        "name": "OWASP",
        "url": "https://owasp.org/events/",
        "type": "cybersecurity",
        "enabled": True,
        "priority": 10,
    },
    "null": {
        "name": "Null Community",
        "url": "https://null.community/",
        "type": "cybersecurity",
        "enabled": True,
        "priority": 10,
    },
    "bsides": {
        "name": "BSides",
        "url": "https://www.securitybsides.com/",
        "type": "cybersecurity",
        "enabled": True,
        "priority": 10,
    },
    "meetup": {
        "name": "Meetup",
        "url": "https://www.meetup.com/",
        "type": "community",
        "enabled": True,
        "priority": 8,
    },
    "eventbrite": {
        "name": "Eventbrite",
        "url": "https://www.eventbrite.com/",
        "type": "events",
        "enabled": True,
        "priority": 8,
    },
    "luma": {
        "name": "Luma",
        "url": "https://lu.ma/",
        "type": "events",
        "enabled": True,
        "priority": 8,
    },
}


# ============================================================
# DIRECT SOURCES
# ============================================================

DIRECT_SOURCES: Final[list[dict[str, object]]] = [
    {
        "key": "owasp_events",
        "name": "OWASP Events",
        "url": "https://owasp.org/events/",
        "source": "OWASP",
        "enabled": True,
    },
    {
        "key": "owasp_chapters",
        "name": "OWASP Chapters",
        "url": "https://owasp.org/chapters/",
        "source": "OWASP",
        "enabled": True,
    },
    {
        "key": "null",
        "name": "Null Community",
        "url": "https://null.community/",
        "source": "Null Community",
        "enabled": True,
    },
    {
        "key": "bsides",
        "name": "Security BSides",
        "url": "https://www.securitybsides.com/",
        "source": "BSides",
        "enabled": True,
    },
]


# ============================================================
# SEARCH SOURCES
# ============================================================

SEARCH_SOURCES: Final[list[dict[str, object]]] = [
    {
        "name": "Google News",
        "type": "rss",
        "enabled": True,
    },
    {
        "name": "Eventbrite",
        "type": "search",
        "enabled": True,
    },
    {
        "name": "Meetup",
        "type": "search",
        "enabled": True,
    },
    {
        "name": "Luma",
        "type": "search",
        "enabled": True,
    },
]


# ============================================================
# INDIA — CITIES
# ============================================================

INDIAN_LOCATIONS: Final[list[str]] = [
    "Hyderabad",
    "Bengaluru",
    "Bangalore",
    "Mumbai",
    "Pune",
    "Chennai",
    "Delhi",
    "New Delhi",
    "Noida",
    "Gurugram",
    "Gurgaon",
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
# INDIA — ADDITIONAL CITIES
# ============================================================

INDIAN_CITIES: Final[list[str]] = [
    "Hyderabad",
    "Bengaluru",
    "Bangalore",
    "Mumbai",
    "Pune",
    "Chennai",
    "Delhi",
    "New Delhi",
    "Noida",
    "Gurugram",
    "Gurgaon",
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
    "Mysuru",
    "Mysore",
    "Thiruvananthapuram",
    "Trivandrum",
    "Surat",
    "Vadodara",
    "Nagpur",
    "Nashik",
    "Patna",
    "Bhopal",
    "Ranchi",
    "Guwahati",
    "Kanpur",
    "Agra",
    "Amritsar",
    "Vijayawada",
    "Mangaluru",
    "Mangalore",
    "Dehradun",
]


# ============================================================
# INDIA — STATES / UTs
# ============================================================

INDIAN_STATES: Final[list[str]] = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Delhi",
    "Chandigarh",
    "Jammu and Kashmir",
    "Ladakh",
    "Puducherry",
]


# ============================================================
# CITY → STATE
# ============================================================

CITY_TO_STATE: Final[dict[str, str]] = {
    "Hyderabad": "Telangana",
    "Bengaluru": "Karnataka",
    "Bangalore": "Karnataka",
    "Mumbai": "Maharashtra",
    "Pune": "Maharashtra",
    "Chennai": "Tamil Nadu",
    "Delhi": "Delhi",
    "New Delhi": "Delhi",
    "Noida": "Uttar Pradesh",
    "Gurugram": "Haryana",
    "Gurgaon": "Haryana",
    "Kolkata": "West Bengal",
    "Kochi": "Kerala",
    "Ahmedabad": "Gujarat",
    "Jaipur": "Rajasthan",
    "Chandigarh": "Chandigarh",
    "Bhubaneswar": "Odisha",
    "Lucknow": "Uttar Pradesh",
    "Indore": "Madhya Pradesh",
    "Coimbatore": "Tamil Nadu",
    "Visakhapatnam": "Andhra Pradesh",
    "Mysuru": "Karnataka",
    "Mysore": "Karnataka",
    "Thiruvananthapuram": "Kerala",
    "Trivandrum": "Kerala",
    "Surat": "Gujarat",
    "Vadodara": "Gujarat",
    "Nagpur": "Maharashtra",
    "Nashik": "Maharashtra",
    "Patna": "Bihar",
    "Bhopal": "Madhya Pradesh",
    "Ranchi": "Jharkhand",
    "Guwahati": "Assam",
    "Kanpur": "Uttar Pradesh",
    "Agra": "Uttar Pradesh",
    "Amritsar": "Punjab",
    "Vijayawada": "Andhra Pradesh",
    "Mangaluru": "Karnataka",
    "Mangalore": "Karnataka",
    "Dehradun": "Uttarakhand",
}


# ============================================================
# LOCATION ALIASES
# ============================================================

LOCATION_ALIASES: Final[dict[str, str]] = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "bombay": "Mumbai",
    "mumbai": "Mumbai",
    "madras": "Chennai",
    "chennai": "Chennai",
    "calcutta": "Kolkata",
    "kolkata": "Kolkata",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "new delhi": "Delhi",
    "delhi": "Delhi",
    "mysore": "Mysuru",
    "mysuru": "Mysuru",
    "trivandrum": "Thiruvananthapuram",
    "thiruvananthapuram": "Thiruvananthapuram",
    "mangalore": "Mangaluru",
    "mangaluru": "Mangaluru",
}


# ============================================================
# CYBERSECURITY KEYWORDS
# ============================================================

CYBERSECURITY_KEYWORDS: Final[list[str]] = [
    "cybersecurity",
    "cyber security",
    "information security",
    "infosec",

    "application security",
    "appsec",
    "web security",
    "api security",

    "cloud security",
    "network security",
    "identity security",
    "identity and access management",
    "identity access management",
    "iam",
    "zero trust",

    "ai security",
    "artificial intelligence security",
    "ai cybersecurity",
    "generative ai security",
    "machine learning security",

    "soc",
    "security operations",
    "blue team",
    "red team",
    "incident response",
    "threat intelligence",
    "threat hunting",

    "penetration testing",
    "penetration test",
    "pentesting",
    "ethical hacking",
    "vapt",
    "vulnerability assessment",
    "vulnerability management",

    "bug bounty",
    "bugbounty",

    "digital forensics",
    "digital forensic",
    "dfir",
    "digital investigation",

    "osint",
    "open source intelligence",

    "grc",
    "governance",
    "risk management",
    "cyber risk",
    "information risk",
    "compliance",

    "malware",
    "ransomware",
    "reverse engineering",

    "cyber crime",
    "cybercrime",
    "cyber fraud",

    "ctf",
    "capture the flag",
    "cyber challenge",

    "security engineering",
    "security architecture",
    "security awareness",
    "security testing",
    "security research",
    "secure coding",
    "devsecops",
    "devsecops",
    "sast",
    "dast",
    "sca",
    "container security",
    "kubernetes security",
    "endpoint security",
    "mobile security",
    "iot security",
    "automotive security",
    "industrial control systems security",
    "ics security",
    "ot security",
    "ot cybersecurity",
]


# ============================================================
# EVENT TYPES
# ============================================================

EVENT_TYPES: Final[list[str]] = [
    "event",
    "conference",
    "meetup",
    "workshop",
    "webinar",
    "summit",
    "training",
    "seminar",
    "networking",
    "community event",
    "community meetup",
    "talk",
    "session",
    "roundtable",
    "masterclass",
    "bootcamp",
    "hackathon",
    "ctf",
    "capture the flag",
    "challenge",
]


# ============================================================
# ONLINE EVENT SIGNALS
# ============================================================

ONLINE_KEYWORDS: Final[list[str]] = [
    "online",
    "virtual",
    "remote",
    "webinar",
    "virtual event",
    "online event",
    "online meetup",
    "virtual meetup",
    "zoom",
    "teams",
    "google meet",
]


# ============================================================
# REGISTRATION SIGNALS
# ============================================================

REGISTRATION_KEYWORDS: Final[list[str]] = [
    "register",
    "registration",
    "rsvp",
    "ticket",
    "tickets",
    "book now",
    "sign up",
    "signup",
    "join event",
    "attend",
    "reserve",
    "apply now",
]


# ============================================================
# DATE SIGNALS
# ============================================================

DATE_KEYWORDS: Final[list[str]] = [
    "date",
    "dates",
    "on",
    "from",
    "until",
    "starts",
    "starting",
    "ends",
    "ending",
]


# ============================================================
# PRICE SIGNALS
# ============================================================

FREE_EVENT_KEYWORDS: Final[list[str]] = [
    "free",
    "free event",
    "no cost",
    "complimentary",
]

PAID_EVENT_KEYWORDS: Final[list[str]] = [
    "paid",
    "ticket",
    "tickets",
    "₹",
    "rs.",
    "inr",
    "usd",
    "$",
]


# ============================================================
# SOURCE TRUST SCORES
# ============================================================

TRUSTED_SOURCES: Final[dict[str, int]] = {
    "owasp.org": 30,
    "null.community": 30,
    "securitybsides.com": 30,
    "meetup.com": 20,
    "eventbrite.com": 20,
    "lu.ma": 20,
    "luma.com": 20,
    "github.com": 15,
    "linkedin.com": 15,
}


# ============================================================
# SOURCE SETTINGS
# ============================================================

SOURCE_SETTINGS: Final[dict[str, object]] = {
    "request_timeout": 20,
    "request_delay_seconds": 1,
    "max_results_per_query": 20,
    "max_events_per_source": 100,
    "max_pages_per_source": 10,
    "respect_robots_txt": True,
    "follow_external_links": False,
}


# ============================================================
# USER AGENT / HTTP HEADERS
# ============================================================

HEADERS: Final[dict[str, str]] = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/140.0.0.0 "
        "Safari/537.36"
    ),
    "Accept": (
        "text/html,"
        "application/xhtml+xml,"
        "application/xml;q=0.9,"
        "image/avif,"
        "image/webp,"
        "*/*;q=0.8"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Cache-Control": "no-cache",
}


# ============================================================
# EVENT SCHEMA
# ============================================================

EVENT_FIELDS: Final[list[str]] = [
    "title",
    "date",
    "time",
    "start_date",
    "end_date",
    "city",
    "state",
    "location",
    "venue",
    "organizer",
    "event_type",
    "price",
    "description",
    "registration_url",
    "event_url",
    "source_url",
    "source",
    "published",
    "verification_score",
]


# ============================================================
# NORMALIZED CITY
# ============================================================

def normalize_city(city: str) -> str:
    if not city:
        return ""

    value = city.strip()

    return LOCATION_ALIASES.get(
        value.lower(),
        value,
    )


# ============================================================
# STATE LOOKUP
# ============================================================

def get_state_for_city(city: str) -> str:
    normalized = normalize_city(city)

    return CITY_TO_STATE.get(
        normalized,
        "",
    )


# ============================================================
# LOCATION DETECTION
# ============================================================

def detect_city(text: str) -> str:
    if not text:
        return ""

    text_lower = text.lower()

    # Longer aliases first.
    aliases = sorted(
        LOCATION_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for alias, city in aliases:

        if alias in text_lower:
            return city

    for city in sorted(
        INDIAN_CITIES,
        key=len,
        reverse=True,
    ):

        if city.lower() in text_lower:
            return normalize_city(city)

    return ""


def detect_state(text: str) -> str:
    if not text:
        return ""

    text_lower = text.lower()

    for state in sorted(
        INDIAN_STATES,
        key=len,
        reverse=True,
    ):

        if state.lower() in text_lower:
            return state

    city = detect_city(text)

    if city:
        return get_state_for_city(city)

    return ""


def is_supported_location(text: str) -> bool:
    if not text:
        return False

    text_lower = text.lower()

    for city in INDIAN_CITIES:

        if city.lower() in text_lower:
            return True

    for alias in LOCATION_ALIASES:

        if alias in text_lower:
            return True

    for state in INDIAN_STATES:

        if state.lower() in text_lower:
            return True

    if any(
        term in text_lower
        for term in ONLINE_KEYWORDS
    ):
        return True

    if "india" in text_lower:
        return True

    return False


# ============================================================
# CYBERSECURITY DETECTION
# ============================================================

def contains_cybersecurity_keyword(
    text: str,
) -> bool:

    if not text:
        return False

    text_lower = text.lower()

    return any(
        keyword.lower() in text_lower
        for keyword in CYBERSECURITY_KEYWORDS
    )


# ============================================================
# EVENT TYPE DETECTION
# ============================================================

def detect_event_type(text: str) -> str:

    if not text:
        return ""

    text_lower = text.lower()

    for event_type in sorted(
        EVENT_TYPES,
        key=len,
        reverse=True,
    ):

        if event_type.lower() in text_lower:
            return event_type

    return ""


# ============================================================
# ONLINE EVENT DETECTION
# ============================================================

def is_online_event(text: str) -> bool:

    if not text:
        return False

    text_lower = text.lower()

    return any(
        keyword.lower() in text_lower
        for keyword in ONLINE_KEYWORDS
    )


# ============================================================
# REGISTRATION DETECTION
# ============================================================

def has_registration_signal(
    text: str,
) -> bool:

    if not text:
        return False

    text_lower = text.lower()

    return any(
        keyword.lower() in text_lower
        for keyword in REGISTRATION_KEYWORDS
    )


# ============================================================
# PRICE DETECTION
# ============================================================

def detect_price(text: str) -> str:

    if not text:
        return ""

    text_lower = text.lower()

    for keyword in FREE_EVENT_KEYWORDS:

        if keyword.lower() in text_lower:
            return "Free"

    for keyword in PAID_EVENT_KEYWORDS:

        if keyword.lower() in text_lower:
            return "Paid / Check event page"

    return ""


# ============================================================
# SOURCE LOOKUP
# ============================================================

def get_source(
    source_key: str,
) -> dict[str, object] | None:

    return SOURCES.get(
        source_key
    )


def get_enabled_sources() -> dict[str, dict[str, object]]:

    return {
        key: value
        for key, value in SOURCES.items()
        if value.get("enabled", True)
    }


def get_enabled_direct_sources() -> list[dict[str, object]]:

    return [
        source
        for source in DIRECT_SOURCES
        if source.get("enabled", True)
    ]


def get_source_name(
    source_key: str,
) -> str:

    source = SOURCES.get(
        source_key
    )

    if not source:
        return source_key

    return str(
        source.get(
            "name",
            source_key,
        )
    )


# ============================================================
# TRUST SCORE
# ============================================================

def get_source_trust_score(
    domain: str,
) -> int:

    if not domain:
        return 0

    domain = domain.lower().strip()

    if domain.startswith("www."):
        domain = domain[4:]

    for trusted_domain, score in TRUSTED_SOURCES.items():

        if domain == trusted_domain:
            return score

        if domain.endswith(
            "." + trusted_domain
        ):
            return score

    return 5


# ============================================================
# SEARCH QUERY GENERATOR
# ============================================================

def build_search_queries() -> list[str]:

    queries = []

    # India-wide searches.
    queries.extend(
        [
            "cybersecurity event India",
            "cyber security event India",
            "information security event India",
            "infosec event India",
            "cybersecurity meetup India",
            "cybersecurity conference India",
            "cybersecurity workshop India",
            "cybersecurity webinar India",
            "cybersecurity CTF India",
            "cybersecurity hackathon India",
            "cybersecurity networking India",
        ]
    )

    # City-focused searches.
    for city in INDIAN_LOCATIONS:

        queries.extend(
            [
                f"cybersecurity event {city}",
                f"cybersecurity meetup {city}",
                f"cyber security event {city}",
                f"infosec event {city}",
                f"security conference {city}",
                f"security workshop {city}",
                f"CTF {city}",
                f"cybersecurity networking {city}",
                f"OWASP {city}",
            ]
        )

    # Topic searches.
    important_topics = [
        "application security",
        "cloud security",
        "AI security",
        "SOC",
        "blue team",
        "red team",
        "DFIR",
        "OSINT",
        "threat intelligence",
        "incident response",
        "bug bounty",
        "VAPT",
        "penetration testing",
        "ethical hacking",
        "GRC",
        "IAM",
        "network security",
        "malware",
    ]

    for topic in important_topics:

        queries.append(
            f"{topic} India event"
        )

    # Online.
    queries.extend(
        [
            "online cybersecurity webinar India",
            "virtual cybersecurity event India",
            "online cybersecurity conference India",
            "online cybersecurity workshop India",
        ]
    )

    return list(
        dict.fromkeys(queries)
    )


# ============================================================
# DEFAULT EVENT
# ============================================================

def empty_event() -> dict[str, object]:

    return {
        "title": "",
        "date": "",
        "time": "",
        "start_date": "",
        "end_date": "",
        "city": "",
        "state": "",
        "location": "",
        "venue": "",
        "organizer": "",
        "event_type": "",
        "price": "",
        "description": "",
        "registration_url": "",
        "event_url": "",
        "source_url": "",
        "source": "",
        "published": "",
        "verification_score": 0,
    }


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "SOURCES",
    "DIRECT_SOURCES",
    "SEARCH_SOURCES",
    "INDIAN_LOCATIONS",
    "INDIAN_CITIES",
    "INDIAN_STATES",
    "CITY_TO_STATE",
    "LOCATION_ALIASES",
    "CYBERSECURITY_KEYWORDS",
    "EVENT_TYPES",
    "ONLINE_KEYWORDS",
    "REGISTRATION_KEYWORDS",
    "DATE_KEYWORDS",
    "FREE_EVENT_KEYWORDS",
    "PAID_EVENT_KEYWORDS",
    "TRUSTED_SOURCES",
    "SOURCE_SETTINGS",
    "HEADERS",
    "EVENT_FIELDS",
    "normalize_city",
    "get_state_for_city",
    "detect_city",
    "detect_state",
    "is_supported_location",
    "contains_cybersecurity_keyword",
    "detect_event_type",
    "is_online_event",
    "has_registration_signal",
    "detect_price",
    "get_source",
    "get_enabled_sources",
    "get_enabled_direct_sources",
    "get_source_name",
    "get_source_trust_score",
    "build_search_queries",
    "empty_event",
]
