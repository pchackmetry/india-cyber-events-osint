import os
import requests

# Telegram bot token is stored securely in GitHub Secrets
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is missing")


def test_bot():

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"

    response = requests.get(url, timeout=20)

    response.raise_for_status()

    data = response.json()

    print("===== TELEGRAM BOT TEST =====")

    if data.get("ok"):
        bot = data["result"]

        print("✅ Bot connection successful")
        print(f"Bot name: {bot.get('first_name')}")
        print(f"Bot username: @{bot.get('username')}")
    else:
        print("❌ Telegram rejected the bot token")
        print(data)


def get_updates():

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

    response = requests.get(url, timeout=20)

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
        print("Post a new message in your Telegram channel")
        print("and run this GitHub Action again.")
        return

    for update in updates:

        print("\n----------------------------")

        print(f"Update ID: {update.get('update_id')}")

        if "channel_post" in update:

            post = update["channel_post"]
            chat = post.get("chat", {})

            print("TYPE: CHANNEL POST")
            print(f"Channel name: {chat.get('title')}")
            print(f"Channel username: @{chat.get('username')}")
            print(f"Channel type: {chat.get('type')}")
            print(f"CHANNEL ID: {chat.get('id')}")
            print(f"Message: {post.get('text')}")

        elif "message" in update:

            message = update["message"]
            chat = message.get("chat", {})

            print("TYPE: MESSAGE")
            print(f"Chat name: {chat.get('title')}")
            print(f"Chat type: {chat.get('type')}")
            print(f"CHAT ID: {chat.get('id')}")
            print(f"Message: {message.get('text')}")

        else:

            print("Other update received")


if __name__ == "__main__":

    print("========================================")
    print(" INDIA CYBERSECURITY OSINT BOT")
    print(" TELEGRAM CONNECTION TEST")
    print("========================================")

    test_bot()

    get_updates()

    print("\n========================================")
    print(" TEST FINISHED")
    print("========================================")
