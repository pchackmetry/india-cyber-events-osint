import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

from sources import INDIAN_LOCATIONS, CYBERSECURITY_KEYWORDS


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    )
}


def search_duckduckgo(query):
    """
    Search DuckDuckGo's public HTML results.

    No search API key is required.
    """

    url = (
        "https://html.duckduckgo.com/html/"
        f"?q={quote(query)}"
    )

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"❌ Search failed: {error}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    results = []

    for result in soup.select(".result"):

        title_element = result.select_one(".result__title")

        link_element = result.select_one(".result__a")

        snippet_element = result.select_one(".result__snippet")

        if not title_element or not link_element:
            continue

        title = title_element.get_text(
            " ",
            strip=True
        )

        link = link_element.get("href")

        snippet = ""

        if snippet_element:
            snippet = snippet_element.get_text(
                " ",
                strip=True
            )

        if link:
            results.append({
                "title": title,
                "url": link,
                "snippet": snippet
            })

    return results


def build_search_queries():

    queries = []

    # General India searches
    queries.extend([
        '"cybersecurity" event India',
        '"cyber security" meetup India',
        '"information security" event India',
        '"infosec" meetup India',
        '"cybersecurity conference" India',
        '"cybersecurity workshop" India',
        '"cybersecurity CTF" India',
        '"security meetup" India'
    ])

    # Location-specific searches
    for location in INDIAN_LOCATIONS:

        queries.extend([
            f'"cybersecurity" event "{location}"',
            f'"cyber security" meetup "{location}"',
            f'"infosec" meetup "{location}"',
            f'"cybersecurity conference" "{location}"'
        ])

    # Important communities
    queries.extend([
        '"OWASP" India event',
        '"OWASP" Hyderabad event',
        '"OWASP" Bengaluru event',
        '"OWASP" Mumbai event',
        '"OWASP" Pune event',
        '"Null community" India cybersecurity',
        '"BSides" India cybersecurity',
        '"cybersecurity" "Luma" India',
        '"cybersecurity" "Meetup" India'
    ])

    # Remove duplicates while preserving order
    return list(dict.fromkeys(queries))


def looks_like_cybersecurity_event(title, snippet):

    text = f"{title} {snippet}".lower()

    # Must contain at least one cybersecurity keyword
    has_cyber_keyword = any(
        keyword.lower() in text
        for keyword in CYBERSECURITY_KEYWORDS
    )

    if not has_cyber_keyword:
        return False

    # Must contain an event-related term
    event_words = [
        "event",
        "meetup",
        "conference",
        "workshop",
        "summit",
        "webinar",
        "ctf",
        "hackathon",
        "networking",
        "seminar",
        "community"
    ]

    return any(
        word in text
        for word in event_words
    )


def discover_events():

    queries = build_search_queries()

    print(f"🔎 Search queries: {len(queries)}")

    discovered = []

    # Limit initial scan so we don't hammer the search engine.
    # We'll increase coverage later.
    for index, query in enumerate(queries[:25], start=1):

        print(
            f"\n[{index}/{min(len(queries), 25)}] "
            f"Searching: {query}"
        )

        results = search_duckduckgo(query)

        print(f"   Results found: {len(results)}")

        for result in results:

            if not looks_like_cybersecurity_event(
                result["title"],
                result["snippet"]
            ):
                continue

            discovered.append({
                "title": result["title"],
                "url": result["url"],
                "snippet": result["snippet"],
                "search_query": query
            })

    # Deduplicate URLs in memory only
    unique = {}

    for event in discovered:

        url = event["url"].split("#")[0]

        if url not in unique:
            unique[url] = event

    events = list(unique.values())

    print("\n========================================")
    print(f"🔎 DISCOVERED EVENTS: {len(events)}")
    print("========================================")

    for number, event in enumerate(events, start=1):

        print(f"\n{number}. {event['title']}")
        print(f"   URL: {event['url']}")
        print(f"   Source query: {event['search_query']}")

    return events


if __name__ == "__main__":

    discover_events()
