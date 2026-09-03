from __future__ import annotations

import os
import requests


TELEGRAM_API = "https://api.telegram.org"


def send_telegram(message: str) -> bool:

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

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=20,
        )

        if response.ok:

            print(
                "✅ Telegram alert sent"
            )

            return True

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


def send_event_alert(event: dict) -> bool:

    message = (
        "🔐 CYBERSECURITY EVENT\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        f"📌 {event['title']}\n\n"

        f"🌐 Source: "
        f"{event['source']}\n"

        f"🔎 Verification: "
        f"{event['verification_score']}/100\n\n"

        f"📝 Registration: "
        f"{event['has_registration']}\n"

        f"📅 Date detected: "
        f"{event['has_date']}\n"

        f"⏳ Future date: "
        f"{event.get('has_future_date', False)}\n"

        f"📍 Location detected: "
        f"{event['has_location']}\n\n"

        f"🔗 Event page:\n"
        f"{event['url']}\n"
    )

    return send_telegram(message)
