from __future__ import annotations

import os
import requests


TELEGRAM_API = "https://api.telegram.org"
MAX_MESSAGE_LENGTH = 4000


def send_telegram(message: str) -> bool:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN is missing")
        return False

    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID is missing")
        return False

    url = f"{TELEGRAM_API}/bot{bot_token}/sendMessage"

    # Split long messages into safe Telegram-sized chunks.
    chunks = []

    while len(message) > MAX_MESSAGE_LENGTH:

        split_at = message.rfind(
            "\n\n",
            0,
            MAX_MESSAGE_LENGTH,
        )

        if split_at == -1:
            split_at = message.rfind(
                "\n",
                0,
                MAX_MESSAGE_LENGTH,
            )

        if split_at == -1:
            split_at = MAX_MESSAGE_LENGTH

        chunks.append(
            message[:split_at]
        )

        message = message[split_at:].lstrip()

    if message:
        chunks.append(message)

    print(
        f"📨 Telegram messages to send: "
        f"{len(chunks)}"
    )

    success = True

    for number, chunk in enumerate(
        chunks,
        start=1,
    ):

        payload = {
            "chat_id": chat_id,
            "text": chunk,
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
                    f"✅ Telegram message "
                    f"{number}/{len(chunks)} sent"
                )

            else:

                print(
                    f"❌ Telegram message "
                    f"{number}/{len(chunks)} failed: "
                    f"{response.status_code} "
                    f"{response.text}"
                )

                success = False

        except requests.RequestException as exc:

            print(
                f"❌ Telegram request failed: "
                f"{exc}"
            )

            success = False

    return success
