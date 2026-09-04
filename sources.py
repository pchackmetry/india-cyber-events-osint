
import os
from html import escape
from urllib.parse import quote

from telegram import Bot
from telegram.error import TelegramError


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def clean(value, default="TBA"):
    if value is None:
        return default

    value = str(value).strip()

    return value if value else default


def html(value, default="TBA"):
    return escape(clean(value, default))


def valid_url(url):
    if not url:
        return False

    url = str(url).strip()

    return url.startswith(("http://", "https://"))


def get_event_url(event):
    urls = [
        event.get("registration_url"),
        event.get("event_url"),
        event.get("url"),
        event.get("link"),
        event.get("source_url"),
    ]

    for url in urls:
        if valid_url(url):
            return str(url).strip()

    return None


def create_google_maps_link(event):
    parts = []

    venue = event.get("venue")
    location = event.get("location")
    city = event.get("city")
    state = event.get("state")

    for value in [venue, location, city, state]:
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


def format_telegram_message(event):

    title = html(
        event.get("title"),
        "Cybersecurity Event"
    )

    date = html(
        event.get("date"),
        "TBA"
    )

    time = html(
        event.get("time"),
        "TBA"
    )

    city = html(
        event.get("city"),
        "TBA"
    )

    state = html(
        event.get("state"),
        ""
    )

    location = html(
        event.get("location"),
        "TBA"
    )

    venue = html(
        event.get("venue"),
        "TBA"
    )

    organizer = html(
        event.get("organizer"),
        "TBA"
    )

    event_type = html(
        event.get("event_type"),
        "Cybersecurity Event"
    )

    price = html(
        event.get("price"),
        "Check event page"
    )

    description = html(
        event.get("description"),
        "No description available."
    )

    source = html(
        event.get("source"),
        "Unknown"
    )

    event_url = get_event_url(event)

    maps_url = create_google_maps_link(event)

    message = f"""🚨 <b>INDIA CYBER EVENT</b>

🛡️ <b>{title}</b>

━━━━━━━━━━━━━━━━━━

📅 <b>Date:</b> {date}
⏰ <b>Time:</b> {time}

📍 <b>City:</b> {city}"""

    if state:
        message += f"""
🏳️ <b>State:</b> {state}"""

    message += f"""
🏢 <b>Venue:</b> {venue}
📌 <b>Location:</b> {location}

👤 <b>Organizer:</b> {organizer}
🎯 <b>Type:</b> {event_type}
💰 <b>Entry:</b> {price}

📝 <b>Details:</b>
{description}

"""

    if event_url:
        message += (
            f'🔗 <b>Event:</b> '
            f'<a href="{escape(event_url, quote=True)}">'
            f'View Event / Register</a>\n\n'
        )
    else:
        message += "🔗 <b>Event:</b> Link not available\n\n"

    if maps_url:
        message += (
            f'🗺️ <b>Location:</b> '
            f'<a href="{escape(maps_url, quote=True)}">'
            f'Open in Google Maps</a>\n\n'
        )

    source_url = event.get("source_url")

    if valid_url(source_url):
        message += (
            f'🌐 <b>Source:</b> '
            f'<a href="{escape(source_url, quote=True)}">'
            f'{source}</a>\n'
        )
    else:
        message += f"🌐 <b>Source:</b> {source}\n"

    message += """
━━━━━━━━━━━━━━━━━━
🇮🇳 <b>India Cyber Events OSINT</b>
"""

    return message.strip()


async def send_telegram_event(event):

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

    if not TELEGRAM_CHAT_ID:
        raise ValueError(
            "TELEGRAM_CHAT_ID is not configured."
        )

    message = format_telegram_message(event)

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


async def send_telegram_events(events):

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

    if not TELEGRAM_CHAT_ID:
        raise ValueError(
            "TELEGRAM_CHAT_ID is not configured."
        )

    bot = Bot(
        token=TELEGRAM_BOT_TOKEN
    )

    sent = 0
    failed = 0

    for event in events:

        message = format_telegram_message(event)

        try:

            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=False
            )

            sent += 1

        except TelegramError as error:

            failed += 1

            print(
                f"[TELEGRAM ERROR] "
                f"{event.get('title', 'Unknown Event')}: "
                f"{error}"
            )

    return {
        "sent": sent,
        "failed": failed
    }


if __name__ == "__main__":

    import asyncio

    test_event = {
        "title": "Cybersecurity Meetup Hyderabad",
        "date": "12 September 2026",
        "time": "10:00 AM - 2:00 PM",
        "city": "Hyderabad",
        "state": "Telangana",
        "location": "Knowledge City, Hyderabad, Telangana",
        "venue": "T-Hub",
        "organizer": "OWASP Hyderabad",
        "event_type": "Meetup",
        "price": "Free",
        "description": (
            "Cybersecurity community meetup covering "
            "application security, threat intelligence, "
            "OSINT and security engineering."
        ),
        "registration_url": "https://example.com/register",
        "source_url": "https://owasp.org/events/",
        "source": "OWASP"
    }

    print(
        format_telegram_message(test_event)
    )

    # Uncomment to send the test event:
    #
    # asyncio.run(
    #     send_telegram_event(test_event)
    # )
