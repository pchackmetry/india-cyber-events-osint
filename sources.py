```python
"""
India Cybersecurity Event OSINT
Telegram Notification Module

Features:
- Rich Telegram event messages
- Clickable event/registration URL
- Clickable Google Maps location
- Location, venue, organizer, type, price and description
- Safe HTML escaping
- Handles missing event fields
"""

import os
from urllib.parse import quote
from html import escape

from telegram import Bot
from telegram.error import TelegramError


# ============================================================
# TELEGRAM CONFIGURATION
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ============================================================
# VALIDATION
# ============================================================

def validate_telegram_config():
    """
    Make sure Telegram configuration exists.
    """

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN environment variable is missing."
        )

    if not TELEGRAM_CHAT_ID:
        raise ValueError(
            "TELEGRAM_CHAT_ID environment variable is missing."
        )


# ============================================================
# GOOGLE MAPS
# ============================================================

def create_google_maps_link(event):
    """
    Create a Google Maps search URL using the most detailed
    location information available.
    """

    location = event.get("location")
    venue = event.get("venue")
    city = event.get("city")

    parts = []

    if venue:
        parts.append(str(venue))

    if location and location not in parts:
        parts.append(str(location))

    if city and city not in parts:
        parts.append(str(city))

    if not parts:
        return None

    search_location = ", ".join(parts)

    return (
        "https://www.google.com/maps/search/"
        "?api=1&query="
        + quote(search_location)
    )


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_value(value, default="TBA"):
    """
    Return a clean string for Telegram.
    """

    if value is None:
        return default

    value = str(value).strip()

    if not value:
        return default

    return value


def safe_html(value, default="TBA"):
    """
    Escape user/event data so special HTML characters do not
    break Telegram formatting.
    """

    return escape(clean_value(value, default))


# ============================================================
# URL HELPERS
# ============================================================

def valid_url(url):
    """
    Basic URL validation.
    """

    if not url:
        return False

    url = str(url).strip()

    return (
        url.startswith("http://")
        or url.startswith("https://")
    )


# ============================================================
# EVENT LINK
# ============================================================

def get_event_url(event):
    """
    Select the best available event URL.

    Priority:
    1. registration_url
    2. event_url
    3. url
    4. source_url
    """

    possible_urls = [
        event.get("registration_url"),
        event.get("event_url"),
        event.get("url"),
        event.get("source_url"),
    ]

    for url in possible_urls:
        if valid_url(url):
            return str(url).strip()

    return None


# ============================================================
# TELEGRAM MESSAGE FORMATTER
# ============================================================

def format_event_message(event):
    """
    Convert an event dictionary into a rich Telegram message.

    Expected event structure:

    {
        "title": "...",
        "date": "...",
        "time": "...",
        "location": "...",
        "city": "...",
        "venue": "...",
        "organizer": "...",
        "event_type": "...",
        "price": "...",
        "description": "...",
        "registration_url": "...",
        "event_url": "...",
        "source_url": "...",
        "source": "..."
    }
    """

    # --------------------------------------------------------
    # BASIC DATA
    # --------------------------------------------------------

    title = safe_html(
        event.get("title"),
        "Cybersecurity Event"
    )

    date = safe_html(
        event.get("date"),
        "TBA"
    )

    time = safe_html(
        event.get("time"),
        "TBA"
    )

    city = safe_html(
        event.get("city"),
        "TBA"
    )

    location = safe_html(
        event.get("location"),
        "TBA"
    )

    venue = safe_html(
        event.get("venue"),
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

    # --------------------------------------------------------
    # EVENT URL
    # --------------------------------------------------------

    event_url = get_event_url(event)

    # --------------------------------------------------------
    # GOOGLE MAPS
    # --------------------------------------------------------

    maps_url = create_google_maps_link(event)

    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    message = f"""
🚨 <b>INDIA CYBER EVENT</b>

🛡️ <b>{title}</b>

━━━━━━━━━━━━━━━━━━

📅 <b>Date:</b> {date}
⏰ <b>Time:</b> {time}

📍 <b>City:</b> {city}
🏢 <b>Venue:</b> {venue}
📌 <b>Location:</b> {location}

👤 <b>Organizer:</b> {organizer}
🎯 <b>Type:</b> {event_type}
💰 <b>Entry:</b> {price}

📝 <b>Details:</b>
{description}

"""

    # --------------------------------------------------------
    # EVENT LINK
    # --------------------------------------------------------

    if event_url:

        safe_event_url = escape(event_url, quote=True)

        message += (
            f'🔗 <b>Event:</b> '
            f'<a href="{safe_event_url}">View Event / Register</a>\n\n'
        )

    else:

        message += (
            "🔗 <b>Event:</b> Link not available\n\n"
        )

    # --------------------------------------------------------
    # GOOGLE MAPS LINK
    # --------------------------------------------------------

    if maps_url:

        safe_maps_url = escape(
            maps_url,
            quote=True
        )

        message += (
            f'🗺️ <b>Location:</b> '
            f'<a href="{safe_maps_url}">Open in Google Maps</a>\n\n'
        )

    # --------------------------------------------------------
    # SOURCE
    # --------------------------------------------------------

    source_url = event.get("source_url")

    if valid_url(source_url):

        safe_source_url = escape(
            source_url,
            quote=True
        )

        message += (
            f'🌐 <b>Source:</b> '
            f'<a href="{safe_source_url}">{source}</a>\n'
        )

    else:

        message += (
            f"🌐 <b>Source:</b> {source}\n"
        )

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    message += """
━━━━━━━━━━━━━━━━━━
🇮🇳 <b>India Cyber Events OSINT</b>
"""

    return message.strip()


# ============================================================
# SEND TELEGRAM MESSAGE
# ============================================================

async def send_telegram_event(event):
    """
    Send one event to Telegram.
    """

    validate_telegram_config()

    message = format_event_message(event)

    bot = Bot(
        token=TELEGRAM_BOT_TOKEN
    )

    try:

        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=False
        )

        return True

    except TelegramError as error:

        print(
            f"[TELEGRAM ERROR] {error}"
        )

        return False


# ============================================================
# SEND MULTIPLE EVENTS
# ============================================================

async def send_telegram_events(events):
    """
    Send multiple events.

    events must be a list of dictionaries.
    """

    validate_telegram_config()

    bot = Bot(
        token=TELEGRAM_BOT_TOKEN
    )

    success_count = 0
    failed_count = 0

    for event in events:

        message = format_event_message(event)

        try:

            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=False
            )

            success_count += 1

        except TelegramError as error:

            failed_count += 1

            print(
                f"[TELEGRAM ERROR] "
                f"{event.get('title', 'Unknown Event')}: "
                f"{error}"
            )

    print(
        f"[TELEGRAM] "
        f"Sent: {success_count} | "
        f"Failed: {failed_count}"
    )

    return {
        "sent": success_count,
        "failed": failed_count
    }


# ============================================================
# TEST EVENT
# ============================================================

TEST_EVENT = {
    "title": "Cybersecurity Community Meetup Hyderabad",

    "date": "12 September 2026",

    "time": "10:00 AM – 2:00 PM",

    "city": "Hyderabad",

    "location": "Knowledge City, Hyderabad, Telangana",

    "venue": "T-Hub",

    "organizer": "OWASP Hyderabad",

    "event_type": "Meetup",

    "price": "Free",

    "description": (
        "A cybersecurity community meetup covering "
        "application security, threat intelligence, "
        "and security engineering."
    ),

    "registration_url": (
        "https://example.com/register"
    ),

    "source_url": (
        "https://owasp.org/events/"
    ),

    "source": "OWASP"
}


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    print(
        format_event_message(
            TEST_EVENT
        )
    )
```
