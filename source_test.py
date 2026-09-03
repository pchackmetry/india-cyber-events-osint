import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

URLS = {
    "Google News RSS": (
        "https://news.google.com/rss/search"
        "?q=cybersecurity+event+India"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    ),

    "OWASP": "https://owasp.org/events/",

    "Null Community": "https://null.community/",

    "BSides": "https://www.securitybsides.com/",
}


for name, url in URLS.items():

    print()
    print("=" * 60)
    print(name)
    print(url)
    print("=" * 60)

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
        )

        print(
            f"HTTP STATUS: {response.status_code}"
        )

        print(
            f"CONTENT LENGTH: {len(response.text)}"
        )

        if response.ok:
            print("✅ ACCESSIBLE")
        else:
            print("❌ NOT OK")

    except Exception as error:

        print("❌ ERROR")
        print(error)
