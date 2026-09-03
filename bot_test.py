import os
import requests

# ============================================================
# TELEGRAM CONFIGURATION
# ============================================================

# Bot token comes from GitHub Secret
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Channel ID comes from GitHub Secret
# Example: -1001234567890
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


# ============================================================
# CHECK BOT TOKEN
# ============================================================

if not BOT_TOKEN:
    raise ValueError(
        "TELEGRAM_BOT_TOKEN is missing. "
        "Add it under GitHub Settings → Secrets and variables → Actions."
    )


# ============================================================
# FUNCTION 1 — TEST BOT CONNECTION
# ============================================================

def test_bot():

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"

    response = requests.get(
        url,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    print("\n===== TELEGRAM BOT TEST =====")

    if data.get("ok"):
        bot = data["result"]

        print("✅ Bot connection successful")
        print(f"Bot name: {bot.get('first_name')}")
        print(f"Bot username: @{bot.get('username')}")
    else:
        print("❌ Telegram rejected the bot token")
        print(data)

        raise RuntimeError("Telegram bot authentication failed")


# ============================================================
# FUNCTION 2 — GET TELEGRAM UPDATES
# ============================================================

def get_updates():

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

    response = requests.get(
        url,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    print("\n===== TELEGRAM UPDATES =====")

    if not data.get("ok"):
        print("❌ Could not retrieve Telegram updates")
        print(data)
        return

    updates = data.get("result", [])

    if not updates:
        print("ℹ️ No updates received.")
        print()
        print("Make sure you have:")
        print("1. Added the bot as administrator of your channel")
        print("2. Given the bot permission to post messages")
        print("3. Posted a new message in the channel")
        return

    for update in updates:

        print("\n----------------------------")

        print(f"Update ID: {update.get('update_id')}")

        # Channel post
        if "channel_post" in update:

            post = update["channel_post"]
            chat = post.get("chat", {})

            print("TYPE: CHANNEL POST")
            print(f"Channel name: {chat.get('title')}")
            print(f"Channel username: @{chat.get('username')}")
            print(f"Channel type: {chat.get('type')}")
            print(f"CHANNEL ID: {chat.get('id')}")
            print(f"Message: {post.get('text')}")

        # Normal message
        elif "message" in update:

            message = update["message"]
            chat = message.get("chat", {})

            print("TYPE: MESSAGE")
            print(f"Chat name: {chat.get('title') or chat.get('first_name')}")
            print(f"Chat type: {chat.get('type')}")
            print(f"CHAT ID: {chat.get('id')}")
            print(f"Message: {message.get('text')}")

        else:

            print("Other update:")
            print(update)


# ============================================================
# FUNCTION 3 — SEND TEST MESSAGE
# ============================================================

def send_test_message():

    if not CHAT_ID:

        print("\n⚠️ TELEGRAM_CHAT_ID is not configured yet.")
        print("Skipping message sending.")
        print("First find your channel ID from the output above.")

        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    message = """🤖 INDIA CYBERSECURITY OSINT BOT

✅ Telegram connection successful

☁️ Cloud: GitHub Actions
🇮🇳 Project: India Cybersecurity Events
🔎 OSINT Engine: Initial setup

This is a test message.

The bot is ready for the next stage.
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

    print("\n===== MESSAGE TEST =====")

    if data.get("ok"):
        print("✅ Test message sent successfully!")
    else:
        print("❌ Failed to send message")
        print(data)


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    print("========================================")
    print(" INDIA CYBERSECURITY OSINT BOT")
    print(" TELEGRAM CONNECTION TEST")
    print("========================================")

    # Test bot authentication
    test_bot()

    # Find channel/chat ID
    get_updates()

    # Send test message if CHAT_ID exists
    send_test_message()

    print("\n========================================")
    print(" TEST FINISHED")
    print("========================================")
