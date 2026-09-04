from __future__ import annotations

import html
import os
import time
from urllib.parse import quote

import requests


# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_API_URL = (
    "https://api.telegram.org/bot{}/sendMessage"
)

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
    Safely retrieve an event value.
    """

    value = event.get(
        key,
        "",
    )

    if value is None:
        return default

    value = str(value).strip()

    if not value:
        return default

    return value


def escape_html(
    value: object,
) -> str:
    """
    Escape user/event-provided text before placing it
    inside Telegram HTML formatting.

    Telegram HTML requires &, < and > to be escaped.
    """

    if value is None:
        return ""

    return html.escape(
        str(value),
        quote=True,
    )


def shorten_text(
    text: str,
    max_length: int,
) -> str:
    """
    Keep Telegram messages within the allowed size.
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

    return (
        bot_token,
        chat_id,
    )


# ============================================================
# EVENT MODE HELPERS
# ============================================================

def normalize_mode(
    event: dict,
) -> str:
    """
    Normalize event mode.
    """

    mode = safe_get(
        event,
        "event_mode",
        "",
    )

    mode = mode.strip().lower()

    if mode in (
        "online",
        "virtual",
        "remote",
    ):
        return "Online"

    if mode in (
        "offline",
        "in-person",
        "in person",
        "physical",
    ):
        return "Offline"

    if mode == "hybrid":
        return "Hybrid"

    return (
        mode.title()
        if mode
        else "Not specified"
    )


def is_online_event(
    event: dict,
) -> bool:
    """
    Determine whether the event is online/remote/virtual.
    """

    mode = normalize_mode(
        event
    )

    if mode in (
        "Online",
        "Hybrid",
    ):
        return True

    location = safe_get(
        event,
        "event_location",
        "",
    ).lower()

    return any(
        keyword in location
        for keyword in (
            "online",
            "virtual",
            "remote",
        )
    )


# ============================================================
# GOOGLE MAPS
# ============================================================

def create_google_maps_link(
    event: dict,
) -> str:
    """
    Create a Google Maps link only for physical events.

    International online events do NOT receive a Maps link.
    """

    if is_online_event(
        event
    ):
        return ""

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

    for value in (
        venue,
        location,
        city,
        state,
        country,
    ):

        if not value:
            continue

        if value == "Not specified":
            continue

        if value.lower() in (
            part.lower()
            for part in parts
        ):
            continue

        parts.append(
            value
        )

    if not parts:
        return ""

    query = ", ".join(
        parts
    )

    return (
        "https://www.google.com/maps/search/"
        "?api=1"
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
            "",
        )

        if value:

            value = str(
                value
            ).strip()

            if value.startswith(
                (
                    "http://",
                    "https://",
                )
            ):

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
            "",
        )

        if value:

            value = str(
                value
            ).strip()

            if value.startswith(
                (
                    "http://",
                    "https://",
                )
            ):

                return value

    return ""


# ============================================================
# DATE
# ============================================================

def format_event_date(
    event: dict,
) -> str:
    """
    Format event start/end date.
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

    if (
        not start
        or start == "Not specified"
    ):
        return "Not specified"

    if (
        end
        and end != "Not specified"
        and end != start
    ):

        return (
            f"{start} – {end}"
        )

    return start


# ============================================================
# LOCATION
# ============================================================

def format_location(
    event: dict,
) -> str:
    """
    Build a clean human-readable location.

    Avoids duplicated venue/city/country values.
    """

    mode = normalize_mode(
        event
    )

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

    # --------------------------------------------------------
    # Online event
    # --------------------------------------------------------

    if mode == "Online":

        if location:
            location_lower = (
                location.lower()
            )

            if any(
                keyword in location_lower
                for keyword in (
                    "online",
                    "virtual",
                    "remote",
                )
            ):

                return "Online / Virtual"

        return "Online / Virtual"

    # --------------------------------------------------------
    # Hybrid
    # --------------------------------------------------------

    if mode == "Hybrid":

        if location:

            return location

        return "Hybrid"

    # --------------------------------------------------------
    # Physical event
    # --------------------------------------------------------

    parts = []

    # Add venue first.
    if (
        venue
        and venue != "Not specified"
    ):

        parts.append(
            venue
        )

    # Add location only when it isn't already
    # represented by the venue.
    if (
        location
        and location != "Not specified"
    ):

        location_lower = (
            location.lower()
        )

        existing = [
            part.lower()
            for part in parts
        ]

        if location_lower not in existing:

            # Don't repeat a venue that is already
            # contained inside the location.
            if not any(
                venue.lower()
                in location_lower
                for venue in (
                    [venue]
                    if venue
                    else []
                )
            ):

                parts.append(
                    location
                )

    # City.
    if (
        city
        and city != "Not specified"
        and city.lower()
        not in (
            part.lower()
            for part in parts
        )
    ):

        parts.append(
            city
        )

    # State.
    if (
        state
        and state != "Not specified"
        and state.lower()
        not in (
            part.lower()
            for part in parts
        )
    ):

        parts.append(
            state
        )

    # Country.
    if (
        country
        and country != "Not specified"
        and country.lower()
        not in (
            part.lower()
            for part in parts
        )
    ):

        parts.append(
            country
        )

    if parts:

        return ", ".join(
            parts
        )

    return "Not specified"


# ============================================================
# DESCRIPTION
# ============================================================

def get_description(
    event: dict,
) -> str:
    """
    Get a clean event description.
    """

    description = safe_get(
        event,
        "event_description",
        "",
    )

    if (
        not description
        or description == "Not specified"
    ):

        description = safe_get(
            event,
            "description",
            "",
        )

    if (
        not description
        or description == "Not specified"
    ):

        return (
            "No description available."
        )

    return description


# ============================================================
# SOURCE
# ============================================================

def get_source(
    event: dict,
) -> str:

    return safe_get(
        event,
        "source",
        "Unknown",
    )


# ============================================================
# VERIFICATION SCORE
# ============================================================

def get_verification_score(
    event: dict,
) -> str:

    value = event.get(
        "verification_score",
        event.get(
            "score",
            "0",
        ),
    )

    if value is None:
        return "0"

    return str(
        value
    )


# ============================================================
# EVENT ORIGIN LABEL
# ============================================================

def get_origin_label(
    event: dict,
) -> str:
    """
    Explain why this event is allowed.

    India physical:
        🇮🇳 India physical event

    India online:
        🌐 India / online

    International online:
        🌍 International online event

    Hybrid:
        🌐 Hybrid event
    """

    mode = normalize_mode(
        event
    )

    country = safe_get(
        event,
        "event_country",
        "",
    ).lower()

    if mode == "Online":

        if country == "india":

            return (
                "🌐 <b>Online event — India</b>"
            )

        return (
            "🌍 <b>International online event</b>"
        )

    if mode == "Hybrid":

        if country == "india":

            return (
                "🇮🇳 <b>India hybrid event</b>"
            )

        return (
            "🌐 <b>Hybrid cybersecurity event</b>"
        )

    return (
        "🇮🇳 <b>India physical event</b>"
    )


# ============================================================
# MESSAGE BUILDER
# ============================================================

def build_event_message(
    event: dict,
) -> str:
    """
    Build the Telegram cybersecurity event alert.

    All dynamic event data is HTML-escaped.
    """

    # --------------------------------------------------------
    # Raw values
    # --------------------------------------------------------

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

    mode = normalize_mode(
        event
    )

    venue = safe_get(
        event,
        "event_venue",
        "",
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

    description = get_description(
        event
    )

    source = get_source(
        event
    )

    verification_score = (
        get_verification_score(
            event
        )
    )

    registration_url = (
        get_registration_url(
            event
        )
    )

    event_url = get_event_url(
        event
    )

    maps_url = (
        create_google_maps_link(
            event
        )
    )

    origin_label = (
        get_origin_label(
            event
        )
    )

    # --------------------------------------------------------
    # Escape dynamic text
    # --------------------------------------------------------

    title_html = escape_html(
        title
    )

    date_html = escape_html(
        date_text
    )

    time_html = escape_html(
        event_time
    )

    location_html = escape_html(
        location
    )

    mode_html = escape_html(
        mode
    )

    venue_html = escape_html(
        venue
    )

    organizer_html = escape_html(
        organizer
    )

    event_type_html = escape_html(
        event_type
    )

    price_html = escape_html(
        price
    )

    description_html = escape_html(
        shorten_text(
            description,
            800,
        )
    )

    source_html = escape_html(
        source
    )

    score_html = escape_html(
        verification_score
    )

    # --------------------------------------------------------
    # Build message
    # --------------------------------------------------------

    lines = []

    lines.append(
        "🔐 <b>CYBERSECURITY EVENT</b>"
    )

    lines.append(
        "━━━━━━━━━━━━━━━━━━━━"
    )

    lines.append("")

    lines.append(
        f"📌 <b>{title_html}</b>"
    )

    lines.append("")

    lines.append(
        f"📅 <b>Date:</b> {date_html}"
    )

    lines.append(
        f"🕐 <b>Time:</b> {time_html}"
    )

    lines.append(
        f"📍 <b>Location:</b> {location_html}"
    )

    lines.append(
        f"🌐 <b>Mode:</b> {mode_html}"
    )

    # Venue only for physical/hybrid events.
    if (
        venue
        and venue != "Not specified"
        and mode != "Online"
    ):

        lines.append(
            f"🏢 <b>Venue:</b> "
            f"{venue_html}"
        )

    lines.append(
        f"🏛️ <b>Organizer:</b> "
        f"{organizer_html}"
    )

    lines.append(
        f"🎯 <b>Type:</b> "
        f"{event_type_html}"
    )

    lines.append(
        f"💰 <b>Price:</b> "
        f"{price_html}"
    )

    lines.append("")

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    lines.append(
        "📝 <b>Description:</b>"
    )

    lines.append(
        description_html
    )

    lines.append("")

    # --------------------------------------------------------
    # Registration
    # --------------------------------------------------------

    if registration_url:

        safe_registration_url = (
            escape_html(
                registration_url
            )
        )

        lines.append(
            f'🎟️ <b><a href="'
            f'{safe_registration_url}">'
            f'Register / Tickets'
            f'</a></b>'
        )

    else:

        lines.append(
            "🎟️ <b>Registration:</b> "
            "Not found"
        )

    # --------------------------------------------------------
    # Event page
    # --------------------------------------------------------

    if event_url:

        safe_event_url = (
            escape_html(
                event_url
            )
        )

        lines.append(
            f'🔗 <b><a href="'
            f'{safe_event_url}">'
            f'Event Page'
            f'</a></b>'
        )

    # --------------------------------------------------------
    # Google Maps
    # --------------------------------------------------------

    if maps_url:

        safe_maps_url = (
            escape_html(
                maps_url
            )
        )

        lines.append(
            f'🗺️ <b><a href="'
            f'{safe_maps_url}">'
            f'Google Maps'
            f'</a></b>'
        )

    lines.append("")

    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    lines.append(
        f"🔎 <b>Verification:</b> "
        f"{score_html}/100"
    )

    lines.append(
        f"🌐 <b>Source:</b> "
        f"{source_html}"
    )

    lines.append("")

    # --------------------------------------------------------
    # Origin / eligibility
    # --------------------------------------------------------

    lines.append(
        origin_label
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
    Send a Telegram message through Bot API.
    """

    bot_token, chat_id = (
        get_telegram_credentials()
    )

    if (
        not bot_token
        or not chat_id
    ):

        return False

    url = (
        TELEGRAM_API_URL.format(
            bot_token
        )
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

                try:

                    data = (
                        response.json()
                    )

                except ValueError:

                    data = {}

                if data.get(
                    "ok",
                    False,
                ):

                    print(
                        "✅ Telegram message sent."
                    )

                    return True

                print(
                    "❌ Telegram API "
                    "returned ok=false:"
                )

                print(
                    data
                )

            else:

                print(
                    "⚠️ Telegram HTTP error: "
                    f"{response.status_code}"
                )

                print(
                    response.text[:500]
                )

        except requests.RequestException as exc:

            print(
                "⚠️ Telegram request failed "
                f"(attempt {attempt}/"
                f"{MAX_RETRIES}): "
                f"{exc}"
            )

        if attempt < MAX_RETRIES:

            time.sleep(
                RETRY_DELAY
            )

    print(
        "❌ Telegram message failed "
        "after all retries."
    )

    return False


# ============================================================
# SEND EVENT ALERT
# ============================================================

def send_event_alert(
    event: dict,
) -> bool:
    """
    Build and send an event alert.

    The pipeline should already have verified the event.
    """

    if not isinstance(
        event,
        dict,
    ):

        print(
            "❌ Invalid event object."
        )

        return False

    # --------------------------------------------------------
    # Safety validation
    # --------------------------------------------------------

    is_today = event.get(
        "is_today",
        False,
    )

    if not is_today:

        print(
            "🛑 Telegram blocked: "
            "event is not marked as TODAY."
        )

        return False

    # --------------------------------------------------------
    # Build message
    # --------------------------------------------------------

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
    print()

    # --------------------------------------------------------
    # Send
    # --------------------------------------------------------

    return send_telegram(
        message
    )


# ============================================================
# TEST MESSAGE
# ============================================================

if __name__ == "__main__":

    test_event = {

        "title": (
            "International "
            "Cybersecurity Webinar "
            "2026"
        ),

        "source": (
            "Example International Source"
        ),

        "event_date": (
            "04 September 2026"
        ),

        "event_end_date": "",

        "event_time": (
            "10:00 AM – 12:00 PM"
        ),

        "event_location": (
            "Online"
        ),

        "event_venue": "",

        "event_city": "",

        "event_state": "",

        "event_country": (
            "United States"
        ),

        "event_mode": (
            "Online"
        ),

        "event_organizer": (
            "Example Security Organization"
        ),

        "event_type": (
            "Webinar"
        ),

        "event_price": (
            "Free"
        ),

        "event_description": (
            "An international online "
            "cybersecurity event covering "
            "application security, threat "
            "intelligence and security "
            "operations."
        ),

        "registration_url": (
            "https://example.com/register"
        ),

        "event_url": (
            "https://example.com/event"
        ),

        "verification_score": (
            "100"
        ),

        "is_today": True,
    }

    print()
    print(
        "=" * 70
    )

    print(
        "TELEGRAM TEST MESSAGE"
    )

    print(
        "=" * 70
    )

    test_message = (
        build_event_message(
            test_event
        )
    )

    print(
        test_message
    )

    print(
        "=" * 70
    )
