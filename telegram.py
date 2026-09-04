from __future__ import annotations

import os
import time
from urllib.parse import quote

import requests


# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_API_URL = "https://api.telegram.org/bot{}/sendMessage"

MAX_MESSAGE_LENGTH = 3900

REQUEST_TIMEOUT = 30

MAX_RETRIES = 3

RETRY_DELAY = 3


# ============================================================
# BASIC HELPERS
# ============================================================

def safe_get(
    event: dict,
    key: str,
    default: str = "Not specified",
) -> str:
    """
    Safely get a value from an event dictionary.
    """

    value = event.get(key, "")

    if value is None:
        return default

    value = str(value).strip()

    if not value:
        return default

    return value


def shorten_text(
    text: str,
    max_length: int,
) -> str:
    """
    Keep Telegram messages within a safe length.
    """

    text = str(text).strip()

    if len(text) <= max_length:
        return text

    return (
        text[: max_length - 3].rstrip()
        + "..."
    )


# ============================================================
# TELEGRAM CREDENTIALS
# ============================================================

def get_telegram_credentials():
    """
    Read Telegram credentials from environment variables.
    """

    bot_token = os.getenv(
        "TELEGRAM_BOT_TOKEN"
    )

    chat_id = os.getenv(
        "TELEGRAM_CHAT_ID"
    )

    if not bot_token:
        print(
            "❌ TELEGRAM_BOT_TOKEN "
            "environment variable is missing."
        )

    if not chat_id:
        print(
            "❌ TELEGRAM_CHAT_ID "
            "environment variable is missing."
        )

    return bot_token, chat_id


# ============================================================
# GOOGLE MAPS
# ============================================================

def create_google_maps_link(
    event: dict,
) -> str:
    """
    Create a Google Maps search link only when a physical
    location is available.

    Online events do not receive a Maps link.
    """

    mode = safe_get(
        event,
        "event_mode",
        "",
    ).lower()

    location = safe_get(
        event,
        "event_location",
        "",
    )

    venue = safe_get(
        event,
        "event_venue",
        "",
    )

    city = safe_get(
        event,
        "event_city",
        "",
    )

    state = safe_get(
        event,
        "event_state",
        "",
    )

    country = safe_get(
        event,
        "event_country",
        "",
    )

    # Do not create Maps links for online events.
    if mode in (
        "online",
        "virtual",
    ):
        return ""

    if not location and not venue and not city:
        return ""

    parts = []

    for value in (
        venue,
        location,
        city,
        state,
        country,
    ):

        if value and value != "Not specified":
            parts.append(value)

    if not parts:
        return ""

    query = ", ".join(parts)

    return (
        "https://www.google.com/maps/search/?api=1"
        f"&query={quote(query)}"
    )


# ============================================================
# EVENT URL
# ============================================================

def get_event_url(
    event: dict,
) -> str:
    """
    Return the best available event page URL.
    """

    for key in (
        "event_url",
        "url",
        "link",
    ):

        value = event.get(
            key,
            ""
        )

        if value:

            value = str(
                value
            ).strip()

            if value:
                return value

    return ""


# ============================================================
# REGISTRATION URL
# ============================================================

def get_registration_url(
    event: dict,
) -> str:
    """
    Return direct registration URL when available.
    """

    for key in (
        "registration_url",
        "register_url",
        "registration_link",
    ):

        value = event.get(
            key,
            ""
        )

        if value:

            value = str(
                value
            ).strip()

            if value:
                return value

    return ""


# ============================================================
# DATE FORMAT
# ============================================================

def format_event_date(
    event: dict,
) -> str:
    """
    Format the extracted start/end date.
    """

    start = safe_get(
        event,
        "event_date",
        "",
    )

    end = safe_get(
        event,
        "event_end_date",
        "",
    )

    if not start or start == "Not specified":
        return "Not specified"

    if (
        end
        and end != "Not specified"
        and end != start
    ):
        return f"{start} – {end}"

    return start


# ============================================================
# LOCATION FORMAT
# ============================================================

def format_location(
    event: dict,
) -> str:
    """
    Build a clean human-readable location.
    """

    location = safe_get(
        event,
        "event_location",
        "",
    )

    venue = safe_get(
        event,
        "event_venue",
        "",
    )

    city = safe_get(
        event,
        "event_city",
        "",
    )

    state = safe_get(
        event,
        "event_state",
        "",
    )

    country = safe_get(
        event,
        "event_country",
        "",
    )

    parts = []

    # Physical venue
    if (
        venue
        and venue != "Not specified"
        and venue.lower() not in (
            location.lower(),
            "online",
            "virtual",
            "online / virtual",
        )
    ):
        parts.append(venue)

    # Location
    if (
        location
        and location != "Not specified"
    ):
        if not parts or location.lower() != parts[-1].lower():
            parts.append(location)

    # City
    if (
        city
        and city != "Not specified"
        and city.lower() not in (
            part.lower()
            for part in parts
        )
    ):
        parts.append(city)

    # State
    if (
        state
        and state != "Not specified"
        and state.lower() not in (
            part.lower()
            for part in parts
        )
    ):
        parts.append(state)

    # Country
    if (
        country
        and country != "Not specified"
        and country.lower() not in (
            part.lower()
            for part in parts
        )
    ):
        parts.append(country)

    if parts:
        return ", ".join(parts)

    return "Not specified"


# ============================================================
# MESSAGE BUILDER
# ============================================================

def build_event_message(
    event: dict,
) -> str:
    """
    Build the complete Telegram cybersecurity event alert.
    """

    title = safe_get(
        event,
        "title",
        "Cybersecurity Event",
    )

    date_text = format_event_date(
        event
    )

    event_time = safe_get(
        event,
        "event_time",
        "Not specified",
    )

    location = format_location(
        event
    )

    mode = safe_get(
        event,
        "event_mode",
        "Not specified",
    )

    organizer = safe_get(
        event,
        "event_organizer",
        "Not specified",
    )

    event_type = safe_get(
        event,
        "event_type",
        "Not specified",
    )

    price = safe_get(
        event,
        "event_price",
        "Not specified",
    )

    description = safe_get(
        event,
        "event_description",
        "",
    )

    if not description:

        description = safe_get(
            event,
            "description",
            "No description available.",
        )

    registration_url = (
        get_registration_url(
            event
        )
    )

    event_url = get_event_url(
        event
    )

    source = safe_get(
        event,
        "source",
        "Unknown",
    )

    verification_score = safe_get(
        event,
        "verification_score",
        "0",
    )

    maps_url = create_google_maps_link(
        event
    )

    # ========================================================
    # BUILD MESSAGE
    # ========================================================

    lines = []

    lines.append(
        "🔐 <b>CYBERSECURITY EVENT</b>"
    )

    lines.append(
        "━━━━━━━━━━━━━━━━━━━━"
    )

    lines.append("")

    lines.append(
        f"📌 <b>{title}</b>"
    )

    lines.append("")

    # Date
    lines.append(
        f"📅 <b>Date:</b> {date_text}"
    )

    # Time
    lines.append(
        f"🕐 <b>Time:</b> {event_time}"
    )

    # Location
    lines.append(
        f"📍 <b>Location:</b> {location}"
    )

    # Mode
    lines.append(
        f"🌐 <b>Mode:</b> {mode}"
    )

    # Venue
    venue = safe_get(
        event,
        "event_venue",
        "",
    )

    if venue:
        lines.append(
            f"🏢 <b>Venue:</b> {venue}"
        )

    # Organizer
    lines.append(
        f"🏛️ <b>Organizer:</b> {organizer}"
    )

    # Event type
    lines.append(
        f"🎯 <b>Type:</b> {event_type}"
    )

    # Price
    lines.append(
        f"💰 <b>Price:</b> {price}"
    )

    lines.append("")

    # Description
    lines.append(
        "📝 <b>Description:</b>"
    )

    lines.append(
        shorten_text(
            description,
            800,
        )
    )

    lines.append("")

    # Registration
    if registration_url:

        lines.append(
            f'🎟️ <b><a href="{registration_url}">'
            "Register / Tickets</a></b>"
        )

    else:

        lines.append(
            "🎟️ <b>Registration:</b> "
            "Not found"
        )

    # Event page
    if event_url:

        lines.append(
            f'🔗 <b><a href="{event_url}">'
            "Event Page</a></b>"
        )

    # Maps
    if maps_url:

        lines.append(
            f'🗺️ <b><a href="{maps_url}">'
            "Google Maps</a></b>"
        )

    lines.append("")

    # Verification
    lines.append(
        f"🔎 <b>Verification:</b> "
        f"{verification_score}/100"
    )

    lines.append(
        f"🌐 <b>Source:</b> {source}"
    )

    lines.append("")

    lines.append(
        "🇮🇳 <b>Today-only verified event</b>"
    )

    message = "\n".join(
        lines
    )

    return shorten_text(
        message,
        MAX_MESSAGE_LENGTH,
    )


# ============================================================
# TELEGRAM SENDER
# ============================================================

def send_telegram(
    message: str,
) -> bool:
    """
    Send a message through Telegram Bot API.
    """

    bot_token, chat_id = (
        get_telegram_credentials()
    )

    if not bot_token or not chat_id:

        return False

    url = TELEGRAM_API_URL.format(
        bot_token
    )

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            response = requests.post(
                url,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )

            if response.ok:

                data = response.json()

                if data.get(
                    "ok",
                    False
                ):

                    return True

                print(
                    "❌ Telegram API returned "
                    "ok=false:"
                )

                print(
                    data
                )

            else:

                print(
                    f"⚠️ Telegram HTTP "
                    f"error: "
                    f"{response.status_code}"
                )

                print(
                    response.text[:500]
                )

        except requests.RequestException as exc:

            print(
                f"⚠️ Telegram request "
                f"failed "
                f"(attempt {attempt}/"
                f"{MAX_RETRIES}): "
                f"{exc}"
            )

        if attempt < MAX_RETRIES:

            time.sleep(
                RETRY_DELAY
            )

    return False


# ============================================================
# SEND EVENT ALERT
# ============================================================

def send_event_alert(
    event: dict,
) -> bool:
    """
    Build and send a cybersecurity event alert.

    The pipeline has already performed the TODAY-only
    validation before reaching this function.
    """

    if not isinstance(
        event,
        dict
    ):

        print(
            "❌ Invalid event object."
        )

        return False

    # Final safety check
    if not event.get(
        "is_today",
        False
    ):

        print(
            "🛑 Telegram blocked: "
            "event is not marked as TODAY."
        )

        return False

    message = build_event_message(
        event
    )

    print()
    print(
        "📨 Telegram message:"
    )
    print(
        message
    )

    return send_telegram(
        message
    )


# ============================================================
# OPTIONAL TEST
# ============================================================

if __name__ == "__main__":

    test_event = {
        "title": (
            "Example Cybersecurity Event"
        ),
        "source": "Example Source",
        "event_date": "04 September 2026",
        "event_end_date": "",
        "event_time": "10:00 AM – 5:00 PM",
        "event_location": "Hyderabad",
        "event_venue": "HICC",
        "event_city": "Hyderabad",
        "event_state": "Telangana",
        "event_country": "India",
        "event_mode": "Offline",
        "event_organizer": "Example Organizer",
        "event_type": "Conference",
        "event_price": "Free",
        "event_description": (
            "Example cybersecurity conference."
        ),
        "registration_url": "",
        "event_url": (
            "https://example.com/event"
        ),
        "verification_score": 100,
        "is_today": True,
    }

    print(
        build_event_message(
            test_event
        )
    )
