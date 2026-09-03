import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is missing")

if not CHAT_ID:
    raise ValueError("TELEGRAM_CHAT_ID is missing")


def test_bot():
    """Check that the Telegram bot token works."""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"

    response = requests.get(url, timeout=20)
    response.raise_for_status()

    data = response.json()

    if not data.get("ok"):
        raise RuntimeError(f"Telegram bot authentication failed: {data}")

    bot = data["result"]

    print("✅ Telegram bot connection successful")
    print(f"Bot name: {bot.get('first_name')}")
    print(f"Bot username: @{bot.get('username')}")


def send_test_message():
    """Send one test message to the Telegram channel."""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    message = """🤖 INDIA CYBERSECURITY OSINT BOT

✅ Telegram connection successful

☁️ Cloud: GitHub Actions
🇮🇳 India Cybersecurity Events
🔎 OSINT Engine: Initial setup

This is an automated test message.

Next step:
🔐 Cybersecurity Events
🤝 Networking Opportunities
📍 Location-wise intelligence
"""

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("ok"):
        raise RuntimeError(f"Telegram message failed: {data}")

    print("✅ Test message sent successfully")


if __name__ == "__main__":

    print("========================================")
    print(" INDIA CYBERSECURITY OSINT BOT")
    print(" TELEGRAM TEST")
    print("========================================")

    test_bot()
    send_test_message()

    print("========================================")
    print(" TEST COMPLETED")
    print("========================================")
