from __future__ import annotations

import os
import time
import requests
from urllib.parse import quote


TELEGRAM_API = "https://api.telegram.org"


def send_telegram(message: str) -> bool:
    """
    Send a plain-text message to Telegram.

    Uses:
        TELEGRAM_BOT_TOKEN
        TELEGRAM_CHAT_ID
    """

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN is missing")
        return False

    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID is missing")
        return False

    url = (
        f"{TELEGRAM_API}/bot"
        f"{bot_token}/sendMessage"
    )

    payload = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": False,
    }

    max_retries = 3

    for attempt in range(max_retries):

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=20,
            )

            if response.ok:
                print("✅ Telegram alert sent")

                # Small gap between messages
                time.sleep(1)

                return True

            # Telegram rate limit
            if response.status_code == 429:

                try:
                    data = response.json()

                    retry_after = (
                        data.get("parameters", {})
                        .get("retry_after", 60)
                    )

                except Exception:
                    retry_after = 60

                print(
                    f"⚠️ Telegram rate limit hit. "
                    f"Waiting {retry_after} seconds..."
                )

                time.sleep(retry_after)

                continue

            print(
                f"❌ Telegram error: "
                f"{response.status_code} "
                f"{response.text}"
            )

            return False

        except requests.RequestException as exc:

            print(
                f"❌ Telegram request failed: "
                f"{exc}"
            )

            return False

    print(
        "❌ Telegram failed after "
        f"{max_retries} attempts"
    )

    return False


def create_google_maps_link(event: dict) -> str | None:
    """
    Create a Google Maps search link using available
    event location information.
    """

    parts = []

    for key in (
        "venue",
        "location",
        "city",
        "state",
    ):
        value = event.get(key)

        if value:
            value = str(value).strip()

            if value and value not in parts:
                parts.append(value)

    if not parts:
        return None

    query = ", ".join(parts)

    return (
        "https://www.google.com/maps/search/"
        "?api=1&query="
        + quote(query)
    )


def get_event_value(
    event: dict,
    key: str,
    default: str = "Not available",
) -> str:
    """
    Safely get an event value.

    Prevents Telegram alerts from crashing when
    a source does not provide a particular field.
    """

    value = event.get(key)

    if value is None:
        return default

    value = str(value).strip()

    if not value:
        return default

    return value


def get_event_url(event: dict) -> str:
    """
    Get the best available event/registration URL.
    """

    possible_keys = (
        "registration_url",
        "event_url",
        "url",
        "link",
    )

    for key in possible_keys:

        value = event.get(key)

        if value:
            value = str(value).strip()

            if value.startswith(("http://", "https://")):
                return value

    return "Not available"


def send_event_alert(event: dict) -> bool:
    """
    Format and send a complete cybersecurity event alert.
    """

    # --------------------------------------------------
    # BASIC EVENT INFORMATION
    # --------------------------------------------------

    title = get_event_value(
        event,
        "title",
        "Cybersecurity Event",
    )

    source = get_event_value(
        event,
        "source",
    )

    event_url = get_event_url(event)

    # --------------------------------------------------
    # DATE / TIME
    # --------------------------------------------------

    date = get_event_value(
        event,
        "date",
    )

    time_value = get_event_value(
        event,
        "time",
    )

    # --------------------------------------------------
    # LOCATION
    # --------------------------------------------------

    city = get_event_value(
        event,
        "city",
        "",
    )

    state = get_event_value(
        event,
        "state",
        "",
    )

    venue = get_event_value(
        event,
        "venue",
        "",
    )

    location = get_event_value(
        event,
        "location",
        "",
    )

    # --------------------------------------------------
    # EVENT DETAILS
    # --------------------------------------------------

    organizer = get_event_value(
        event,
        "organizer",
    )

    event_type = get_event_value(
        event,
        "event_type",
    )

    price = get_event_value(
        event,
        "price",
    )

    description = get_event_value(
        event,
        "description",
    )

    # --------------------------------------------------
    # VERIFICATION INFORMATION
    # --------------------------------------------------

    verification_score = event.get(
        "verification_score",
        "N/A",
    )

    has_registration = event.get(
        "has_registration",
        False,
    )

    has_date = event.get(
        "has_date",
        False,
    )

    has_future_date = event.get(
        "has_future_date",
        False,
    )

    has_location = event.get(
        "has_location",
        False,
    )

    # --------------------------------------------------
    # GOOGLE MAPS
    # --------------------------------------------------

    google_maps_url = create_google_maps_link(event)

    # --------------------------------------------------
    # BUILD LOCATION TEXT
    # --------------------------------------------------

    location_parts = []

    if venue and venue != "Not available":
        location_parts.append(f"🏢 Venue: {venue}")

    if location and location != "Not available":
        location_parts.append(
            f"📍 Location: {location}"
        )

    if city and city != "Not available":
        location_parts.append(
            f"🏙️ City: {city}"
        )

    if state and state != "Not available":
        location_parts.append(
            f"🗺️ State: {state}"
        )

    location_text = "\n".join(location_parts)

    if not location_text:
        location_text = "📍 Location: Not available"

    # --------------------------------------------------
    # BUILD TELEGRAM MESSAGE
    # --------------------------------------------------

    message_lines = [
        "🔐 CYBERSECURITY EVENT",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        f"📌 {title}",
        "",
        f"📅 Date: {date}",
        f"🕐 Time: {time_value}",
        "",
        location_text,
        "",
        f"👤 Organizer: {organizer}",
        f"🎯 Type: {event_type}",
        f"💰 Price: {price}",
        "",
        f"📝 Description:",
        description,
        "",
        "🔎 VERIFICATION",
        f"Score: {verification_score}/100",
        f"Registration detected: {has_registration}",
        f"Date detected: {has_date}",
        f"Future date: {has_future_date}",
        f"Location detected: {has_location}",
        "",
    ]

    # --------------------------------------------------
    # EVENT LINK
    # --------------------------------------------------

    if event_url != "Not available":

        message_lines.extend(
            [
                "🔗 EVENT / REGISTRATION",
                event_url,
                "",
            ]
        )

    # --------------------------------------------------
    # GOOGLE MAPS LINK
    # --------------------------------------------------

    if google_maps_url:

        message_lines.extend(
            [
                "🗺️ OPEN IN GOOGLE MAPS",
                google_maps_url,
                "",
            ]
        )

    # --------------------------------------------------
    # SOURCE
    # --------------------------------------------------

    message_lines.extend(
        [
            f"🌐 Source: {source}",
            "",
            "🇮🇳 India Cyber Events OSINT",
        ]
    )

    message = "\n".join(message_lines)

    # --------------------------------------------------
    # SEND
    # --------------------------------------------------

    return send_telegram(message)
