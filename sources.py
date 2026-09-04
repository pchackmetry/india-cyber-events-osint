from __future__ import annotations


# ============================================================
# INDIA CYBERSECURITY EVENT OSINT
# SOURCES CONFIGURATION
# ============================================================


# ============================================================
# EVENT SOURCES
# ============================================================

SOURCES = {
    "owasp": {
        "name": "OWASP",
        "url": "https://owasp.org/events/",
        "type": "cybersecurity",
        "enabled": True,
    },

    "null": {
        "name": "Null Community",
        "url": "https://null.community/",
        "type": "cybersecurity",
        "enabled": True,
    },

    "bsides": {
        "name": "BSides",
        "url": "https://www.securitybsides.com/",
        "type": "cybersecurity",
        "enabled": True,
    },

    "meetup": {
        "name": "Meetup",
        "url": "https://www.meetup.com/",
        "type": "community",
        "enabled": True,
    },

    "eventbrite": {
        "name": "Eventbrite",
        "url": "https://www.eventbrite.com/",
        "type": "events",
        "enabled": True,
    },

    "luma": {
        "name": "Luma",
        "url": "https://lu.ma/",
        "type": "events",
        "enabled": True,
    },
}


# ============================================================
# INDIAN LOCATIONS
# ============================================================

INDIAN_LOCATIONS = [
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
# INDIAN STATES / UNION TERRITORIES
# ============================================================

INDIAN_STATES = [
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
# CITY → STATE MAPPING
# ============================================================

CITY_TO_STATE = {
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
}


# ============================================================
# CYBERSECURITY KEYWORDS
# ============================================================

CYBERSECURITY_KEYWORDS = [
    "cybersecurity",
    "cyber security",
    "information security",
    "infosec",

    # Application Security
    "application security",
    "appsec",
    "web security",
    "API security",

    # Cloud / Infrastructure
    "cloud security",
    "network security",
    "identity security",
    "IAM",
    "zero trust",

    # AI Security
    "AI security",
    "artificial intelligence security",
    "AI cybersecurity",

    # Security Operations
    "SOC",
    "security operations",
    "blue team",
    "incident response",
    "threat intelligence",

    # Offensive Security
    "red team",
    "penetration testing",
    "penetration test",
    "pentesting",
    "ethical hacking",
    "VAPT",
    "vulnerability assessment",

    # Bug Bounty
    "bug bounty",
    "bugbounty",

    # DFIR
    "digital forensics",
    "digital forensic",
    "DFIR",
    "digital investigation",

    # OSINT
    "OSINT",
    "open source intelligence",

    # Governance / Risk / Compliance
    "GRC",
    "governance",
    "risk management",
    "compliance",
    "cyber risk",
    "information risk",

    # Identity
    "identity and access management",
    "identity access management",

    # Malware
    "malware",
    "ransomware",

    # Cybercrime
    "cyber crime",
    "cybercrime",

    # CTF / Hacking
    "CTF",
    "capture the flag",
    "cyber challenge",
]


# ============================================================
# EVENT TYPES
# ============================================================

EVENT_TYPES = [
    "conference",
    "meetup",
    "workshop",
    "webinar",
    "CTF",
    "hackathon",
    "summit",
    "training",
    "networking",
    "community event",
    "seminar",
    "bootcamp",
    "masterclass",
    "talk",
    "discussion",
    "roundtable",
]


# ============================================================
# SOURCE-SPECIFIC SETTINGS
# ============================================================

SOURCE_SETTINGS = {
    "request_timeout": 20,

    "max_events_per_source": 100,

    "max_pages_per_source": 10,

    "respect_robots_txt": True,

    "follow_external_links": False,
}


# ============================================================
# USER AGENT
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/139.0.0.0 "
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
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_enabled_sources() -> dict:
    """
    Return only enabled event sources.
    """

    return {
        key: config
        for key, config in SOURCES.items()
        if config.get("enabled", True)
    }


def get_source(source_key: str) -> dict | None:
    """
    Return configuration for a specific source.
    """

    return SOURCES.get(source_key)


def get_state_for_city(city: str) -> str:
    """
    Return the Indian state associated with a city.
    """

    if not city:
        return ""

    city = city.strip()

    return CITY_TO_STATE.get(city, "")


def is_supported_location(location: str) -> bool:
    """
    Check whether text contains one of the supported
    Indian cities or states.
    """

    if not location:
        return False

    location_lower = location.lower()

    for city in INDIAN_LOCATIONS:
        if city.lower() in location_lower:
            return True

    for state in INDIAN_STATES:
        if state.lower() in location_lower:
            return True

    return False


def contains_cybersecurity_keyword(text: str) -> bool:
    """
    Check whether text contains a cybersecurity keyword.
    """

    if not text:
        return False

    text_lower = text.lower()

    return any(
        keyword.lower() in text_lower
        for keyword in CYBERSECURITY_KEYWORDS
    )


def detect_event_type(text: str) -> str:
    """
    Detect an event type from text.
    """

    if not text:
        return ""

    text_lower = text.lower()

    for event_type in EVENT_TYPES:

        if event_type.lower() in text_lower:
            return event_type

    return ""


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "SOURCES",
    "INDIAN_LOCATIONS",
    "INDIAN_STATES",
    "CITY_TO_STATE",
    "CYBERSECURITY_KEYWORDS",
    "EVENT_TYPES",
    "SOURCE_SETTINGS",
    "HEADERS",
    "get_enabled_sources",
    "get_source",
    "get_state_for_city",
    "is_supported_location",
    "contains_cybersecurity_keyword",
    "detect_event_type",
]
