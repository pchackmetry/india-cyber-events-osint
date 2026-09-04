# ============================================================
# INDIA CYBERSECURITY EVENT OSINT BOT
# Complete Single-File Version
# ============================================================

import os
import re
import json
import time
import hashlib
import logging
from html import escape
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.error import TelegramError


# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DATA_FILE = "events.json"

REQUEST_TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/139.0 Safari/537.36"
    )
}


# ============================================================
# SOURCES
# ============================================================

SOURCES = {

    "owasp": {
        "name": "OWASP",
        "url": "https://owasp.org/events/",
        "type": "cybersecurity"
    },

    "null": {
        "name": "Null Community",
        "url": "https://null.community/",
        "type": "cybersecurity"
    },

    "bsides": {
        "name": "BSides",
        "url": "https://www.securitybsides.com/",
        "type": "cybersecurity"
    },

    "meetup": {
        "name": "Meetup",
        "url": "https://www.meetup.com/",
        "type": "community"
    },

    "eventbrite": {
        "name": "Eventbrite",
        "url": "https://www.eventbrite.com/",
        "type": "events"
    },

    "luma": {
        "name": "Luma",
        "url": "https://lu.ma/",
        "type": "events"
    }
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
    "Visakhapatnam"
]


# ============================================================
# CYBERSECURITY KEYWORDS
# ============================================================

CYBERSECURITY_KEYWORDS = [
    "cybersecurity",
    "cyber security",
    "information security",
    "infosec",
    "application security",
    "appsec",
    "cloud security",
    "AI security",
    "artificial intelligence security",
    "SOC",
    "blue team",
    "red team",
    "penetration testing",
    "pentesting",
    "ethical hacking",
    "digital forensics",
    "DFIR",
    "threat intelligence",
    "incident response",
    "OSINT",
    "bug bounty",
    "vulnerability",
    "VAPT",
    "GRC",
    "risk",
    "compliance",
    "IAM",
    "identity security",
    "network security",
    "CTF",
    "capture the flag",
    "malware",
    "zero trust",
    "security operations",
    "cyber crime",
    "cybercrime",
    "digital investigation"
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
    "seminar"
]


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("india-cyber-events")


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()
session.headers.update(HEADERS)


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_text(value):

    if value is None:
        return ""

    value = str(value)

    value = re.sub(r"\s+", " ", value)

    return value.strip()


def safe_html(value, default="TBA"):

    value = clean_text(value)

    if not value:
        value = default

    return escape(value)


def valid_url(url):

    if not url:
        return False

    url = str(url).strip()

    return url.startswith(
        ("http://", "https://")
    )


# ============================================================
# LOCATION DETECTION
# ============================================================

def detect_city(text):

    if not text:
        return ""

    text_lower = text.lower()

    for city in INDIAN_LOCATIONS:

        if city.lower() in text_lower:

            if city.lower() == "bangalore":
                return "Bengaluru"

            if city.lower() == "gurgaon":
                return "Gurugram"

            if city.lower() == "new delhi":
                return "Delhi"

            return city

    return ""


def detect_state(city):

    states = {

        "Hyderabad": "Telangana",
        "Bengaluru": "Karnataka",
        "Mumbai": "Maharashtra",
        "Pune": "Maharashtra",
        "Chennai": "Tamil Nadu",
        "Delhi": "Delhi",
        "Noida": "Uttar Pradesh",
        "Gurugram": "Haryana",
        "Kolkata": "West Bengal",
        "Kochi": "Kerala",
        "Ahmedabad": "Gujarat",
        "Jaipur": "Rajasthan",
        "Chandigarh": "Chandigarh",
        "Bhubaneswar": "Odisha",
        "Lucknow": "Uttar Pradesh",
        "Indore": "Madhya Pradesh",
        "Coimbatore": "Tamil Nadu",
        "Visakhapatnam": "Andhra Pradesh"
    }

    return states.get(city, "")


def build_location(event):

    parts = []

    for field in [
        "venue",
        "location",
        "city",
        "state"
    ]:

        value = clean_text(
            event.get(field)
        )

        if value and value not in parts:
            parts.append(value)

    return ", ".join(parts)


# ============================================================
# GOOGLE MAPS
# ============================================================

def create_google_maps_link(event):

    location = build_location(event)

    if not location:
        return None

    return (
        "https://www.google.com/maps/search/"
        "?api=1&query="
        + quote(location)
    )


# ============================================================
# EVENT URL
# ============================================================

def get_event_url(event):

    possible_urls = [

        event.get("registration_url"),

        event.get("event_url"),

        event.get("url"),

        event.get("link"),

        event.get("source_url")
    ]

    for url in possible_urls:

        if valid_url(url):
            return str(url).strip()

    return None


# ============================================================
# EVENT ID
# ============================================================

def create_event_id(event):

    identity = "|".join([
        clean_text(event.get("title")).lower(),
        clean_text(event.get("date")).lower(),
        clean_text(event.get("city")).lower(),
        clean_text(event.get("venue")).lower(),
        clean_text(get_event_url(event)).lower()
    ])

    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()


# ============================================================
# EVENT VALIDATION
# ============================================================

def is_cybersecurity_event(event):

    text = " ".join([
        clean_text(event.get("title")),
        clean_text(event.get("description")),
        clean_text(event.get("event_type"))
    ]).lower()

    for keyword in CYBERSECURITY_KEYWORDS:

        if keyword.lower() in text:
            return True

    return False


def is_indian_event(event):

    text = " ".join([
        clean_text(event.get("title")),
        clean_text(event.get("description")),
        clean_text(event.get("location")),
        clean_text(event.get("venue")),
        clean_text(event.get("city")),
        clean_text(event.get("state"))
    ]).lower()

    for location in INDIAN_LOCATIONS:

        if location.lower() in text:
            return True

    return False


# ============================================================
# NORMALIZE EVENT
# ============================================================

def normalize_event(event):

    normalized = {

        "title": clean_text(
            event.get("title")
        ),

        "date": clean_text(
            event.get("date")
        ),

        "time": clean_text(
            event.get("time")
        ),

        "city": clean_text(
            event.get("city")
        ),

        "state": clean_text(
            event.get("state")
        ),

        "location": clean_text(
            event.get("location")
        ),

        "venue": clean_text(
            event.get("venue")
        ),

        "organizer": clean_text(
            event.get("organizer")
        ),

        "event_type": clean_text(
            event.get("event_type")
        ),

        "price": clean_text(
            event.get("price")
        ),

        "description": clean_text(
            event.get("description")
        ),

        "registration_url": clean_text(
            event.get("registration_url")
        ),

        "event_url": clean_text(
            event.get("event_url")
        ),

        "url": clean_text(
            event.get("url")
        ),

        "source_url": clean_text(
            event.get("source_url")
        ),

        "source": clean_text(
            event.get("source")
        )
    }

    combined_location = " ".join([
        normalized["title"],
        normalized["description"],
        normalized["location"],
        normalized["venue"],
        normalized["city"]
    ])

    if not normalized["city"]:

        normalized["city"] = detect_city(
            combined_location
        )

    if not normalized["state"]:

        normalized["state"] = detect_state(
            normalized["city"]
        )

    if not normalized["location"]:

        if normalized["venue"]:
            normalized["location"] = (
                normalized["venue"]
            )

        elif normalized["city"]:
            normalized["location"] = (
                normalized["city"]
            )

    normalized["id"] = create_event_id(
        normalized
    )

    return normalized


# ============================================================
# GENERIC WEBSITE SCRAPER
# ============================================================

def fetch_page(url):

    try:

        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as error:

        logger.error(
            "Failed to fetch %s: %s",
            url,
            error
        )

        return None


def extract_links(url, html_content):

    soup = BeautifulSoup(
        html_content,
        "html.parser"
    )

    links = []

    for anchor in soup.find_all("a"):

        href = anchor.get("href")

        text = clean_text(
            anchor.get_text(" ", strip=True)
        )

        if not href:
            continue

        absolute_url = urljoin(
            url,
            href
        )

        if not valid_url(absolute_url):
            continue

        links.append({
            "title": text,
            "url": absolute_url
        })

    return links


# ============================================================
# GENERIC EVENT EXTRACTION
# ============================================================

def extract_generic_events(
    source_key,
    source_config
):

    source_name = source_config["name"]
    source_url = source_config["url"]

    logger.info(
        "Scanning %s",
        source_name
    )

    html_content = fetch_page(
        source_url
    )

    if not html_content:
        return []

    links = extract_links(
        source_url,
        html_content
    )

    events = []

    for link in links:

        title = clean_text(
            link["title"]
        )

        if len(title) < 5:
            continue

        combined = title.lower()

        cyber_match = any(
            keyword.lower() in combined
            for keyword in CYBERSECURITY_KEYWORDS
        )

        event_match = any(
            event_type.lower() in combined
            for event_type in EVENT_TYPES
        )

        location_match = any(
            location.lower() in combined
            for location in INDIAN_LOCATIONS
        )

        if not (
            cyber_match
            or event_match
            or location_match
        ):
            continue

        event = normalize_event({

            "title": title,

            "event_url": link["url"],

            "source_url": source_url,

            "source": source_name,

            "description": title
        })

        events.append(event)

    return events


# ============================================================
# SPECIALIZED SOURCE SEARCH
# ============================================================

def search_source(
    source_key,
    keyword,
    location
):

    source = SOURCES.get(
        source_key
    )

    if not source:
        return []

    base_url = source["url"]

    query_url = (
        base_url
        + "?q="
        + quote(
            f"{keyword} {location}"
        )
    )

    try:

        response = session.get(
            query_url,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        events = []

        for element in soup.find_all(
            ["article", "div", "li"]
        ):

            text = clean_text(
                element.get_text(
                    " ",
                    strip=True
                )
            )

            if len(text) < 20:
                continue

            if not any(
                keyword.lower()
                in text.lower()
                for keyword in CYBERSECURITY_KEYWORDS
            ):
                continue

            if not any(
                location.lower()
                in text.lower()
                for location in INDIAN_LOCATIONS
            ):
                continue

            link = element.find(
                "a",
                href=True
            )

            event_url = None

            if link:

                event_url = urljoin(
                    base_url,
                    link["href"]
                )

            title = (
                clean_text(
                    link.get_text(
                        " ",
                        strip=True
                    )
                )
                if link
                else text[:150]
            )

            event = normalize_event({

                "title": title,

                "description": text,

                "city": location,

                "event_url": event_url,

                "source_url": base_url,

                "source": source["name"]
            })

            events.append(event)

        return events

    except requests.RequestException:

        return []


# ============================================================
# LOAD STORED EVENTS
# ============================================================

def load_events():

    if not os.path.exists(
        DATA_FILE
    ):
        return {}

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if isinstance(data, dict):
                return data

    except (
        json.JSONDecodeError,
        OSError
    ):
        pass

    return {}


# ============================================================
# SAVE STORED EVENTS
# ============================================================

def save_events(events):

    try:

        with open(
            DATA_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                events,
                file,
                indent=2,
                ensure_ascii=False
            )

    except OSError as error:

        logger.error(
            "Unable to save events: %s",
            error
        )


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate_events(events):

    unique = {}

    for event in events:

        normalized = normalize_event(
            event
        )

        event_id = normalized["id"]

        if event_id not in unique:

            unique[event_id] = normalized

    return list(
        unique.values()
    )


# ============================================================
# TELEGRAM MESSAGE
# ============================================================

def format_telegram_message(event):

    title = safe_html(
        event.get("title"),
        "Cybersecurity Event"
    )

    date = safe_html(
        event.get("date"),
        "TBA"
    )

    event_time = safe_html(
        event.get("time"),
        "TBA"
    )

    city = safe_html(
        event.get("city"),
        "TBA"
    )

    state = clean_text(
        event.get("state")
    )

    venue = safe_html(
        event.get("venue"),
        "TBA"
    )

    location = safe_html(
        event.get("location"),
        "TBA"
    )

    organizer = safe_html(
        event.get("organizer"),
        "TBA"
    )

    event_type = safe_html(
        event.get("event_type"),
        "Cybersecurity Event"
    )

    price = safe_html(
        event.get("price"),
        "Check event page"
    )

    description = safe_html(
        event.get("description"),
        "No description available."
    )

    source = safe_html(
        event.get("source"),
        "Unknown"
    )

    event_url = get_event_url(
        event
    )

    maps_url = create_google_maps_link(
        event
    )

    message = (
        "🚨 <b>INDIA CYBER EVENT</b>\n\n"
        f"🛡️ <b>{title}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 <b>Date:</b> {date}\n"
        f"⏰ <b>Time:</b> {event_time}\n\n"
        f"📍 <b>City:</b> {city}\n"
    )

    if state:

        message += (
            f"🏳️ <b>State:</b> "
            f"{escape(state)}\n"
        )

    message += (
        f"🏢 <b>Venue:</b> {venue}\n"
        f"📌 <b>Location:</b> {location}\n\n"
        f"👤 <b>Organizer:</b> {organizer}\n"
        f"🎯 <b>Type:</b> {event_type}\n"
        f"💰 <b>Entry:</b> {price}\n\n"
        f"📝 <b>Details:</b>\n"
        f"{description}\n\n"
    )

    if event_url:

        message += (
            "🔗 <b>Event:</b> "
            f'<a href="{escape(event_url, quote=True)}">'
            "View Event / Register</a>\n\n"
        )

    else:

        message += (
            "🔗 <b>Event:</b> "
            "Link not available\n\n"
        )

    if maps_url:

        message += (
            "🗺️ <b>Location:</b> "
            f'<a href="{escape(maps_url, quote=True)}">'
            "Open in Google Maps</a>\n\n"
        )

    source_url = event.get(
        "source_url"
    )

    if valid_url(source_url):

        message += (
            "🌐 <b>Source:</b> "
            f'<a href="{escape(source_url, quote=True)}">'
            f"{source}</a>\n"
        )

    else:

        message += (
            f"🌐 <b>Source:</b> "
            f"{source}\n"
        )

    message += (
        "\n━━━━━━━━━━━━━━━━━━\n"
        "🇮🇳 <b>India Cyber Events OSINT</b>"
    )

    return message.strip()


# ============================================================
# TELEGRAM SEND
# ============================================================

async def send_telegram_message(
    bot,
    event
):

    message = format_telegram_message(
        event
    )

    try:

        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=False
        )

        logger.info(
            "Telegram sent: %s",
            event.get("title")
        )

        return True

    except TelegramError as error:

        logger.error(
            "Telegram error: %s",
            error
        )

        return False


# ============================================================
# COLLECT EVENTS
# ============================================================

def collect_events():

    all_events = []

    # --------------------------------------------------------
    # Generic source scanning
    # --------------------------------------------------------

    for source_key, source_config in SOURCES.items():

        try:

            events = extract_generic_events(
                source_key,
                source_config
            )

            all_events.extend(
                events
            )

        except Exception as error:

            logger.exception(
                "Source error %s: %s",
                source_key,
                error
            )

    # --------------------------------------------------------
    # Location + keyword search
    # --------------------------------------------------------

    for source_key in SOURCES:

        for location in INDIAN_LOCATIONS:

            for keyword in CYBERSECURITY_KEYWORDS:

                try:

                    events = search_source(
                        source_key,
                        keyword,
                        location
                    )

                    all_events.extend(
                        events
                    )

                except Exception as error:

                    logger.error(
                        "Search failed: %s",
                        error
                    )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    normalized_events = []

    for event in all_events:

        event = normalize_event(
            event
        )

        if not event.get(
            "title"
        ):
            continue

        if not is_cybersecurity_event(
            event
        ):
            continue

        if not is_indian_event(
            event
        ):
            continue

        normalized_events.append(
            event
        )

    # --------------------------------------------------------
    # Deduplicate
    # --------------------------------------------------------

    return deduplicate_events(
        normalized_events
    )


# ============================================================
# PROCESS EVENTS
# ============================================================

async def process_events():

    if not TELEGRAM_BOT_TOKEN:

        raise ValueError(
            "TELEGRAM_BOT_TOKEN "
            "environment variable is missing."
        )

    if not TELEGRAM_CHAT_ID:

        raise ValueError(
            "TELEGRAM_CHAT_ID "
            "environment variable is missing."
        )

    logger.info(
        "Starting India Cybersecurity "
        "Event OSINT scanner..."
    )

    events = collect_events()

    logger.info(
        "Collected %d events",
        len(events)
    )

    stored_events = load_events()

    bot = Bot(
        token=TELEGRAM_BOT_TOKEN
    )

    new_events = []

    for event in events:

        event_id = event["id"]

        if event_id in stored_events:

            continue

        new_events.append(
            event
        )

    logger.info(
        "New events: %d",
        len(new_events)
    )

    sent = 0

    for event in new_events:

        success = await send_telegram_message(
            bot,
            event
        )

        if success:

            stored_events[
                event["id"]
            ] = event

            sent += 1

        time.sleep(1)

    save_events(
        stored_events
    )

    logger.info(
        "Finished. Sent %d new events.",
        sent
    )

    return {
        "collected": len(events),
        "new": len(new_events),
        "sent": sent
    }


# ============================================================
# TEST TELEGRAM MESSAGE
# ============================================================

TEST_EVENT = {

    "title":
        "Cybersecurity Meetup Hyderabad 2026",

    "date":
        "12 September 2026",

    "time":
        "10:00 AM - 2:00 PM",

    "city":
        "Hyderabad",

    "state":
        "Telangana",

    "location":
        "Knowledge City, Hyderabad, Telangana",

    "venue":
        "T-Hub",

    "organizer":
        "OWASP Hyderabad",

    "event_type":
        "Meetup",

    "price":
        "Free",

    "description":
        (
            "Cybersecurity community meetup "
            "covering application security, "
            "OSINT, threat intelligence and "
            "security engineering."
        ),

    "registration_url":
        "https://example.com/register",

    "source_url":
        "https://owasp.org/events/",

    "source":
        "OWASP"
}


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    import asyncio

    # --------------------------------------------------------
    # TEST MESSAGE
    # --------------------------------------------------------
    #
    # Uncomment this section if you want to test
    # Telegram formatting first.
    #
    # asyncio.run(
    #     send_telegram_message(
    #         Bot(TELEGRAM_BOT_TOKEN),
    #         TEST_EVENT
    #     )
    # )

    # --------------------------------------------------------
    # RUN COMPLETE SCANNER
    # --------------------------------------------------------

    asyncio.run(
        process_events()
    )
