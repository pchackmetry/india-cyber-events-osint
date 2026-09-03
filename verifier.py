"""
Event verification layer.

Checks whether discovered event URLs are reachable and extracts
basic evidence from the actual event page.

This is intentionally separate from discovery so it can be upgraded
later with:
- date extraction
- venue extraction
- registration detection
- cancellation detection
- organizer verification
- cross-source verification
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    )
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


@dataclass
class VerificationResult:
    url: str
    reachable: bool
    status_code: int
    title: str
    text: str
    has_registration_signal: bool
    has_date_signal: bool
    has_location_signal: bool
    verified_at: str


def clean_text(text: str) -> str:
    """Normalize webpage text."""

    text = re.sub(r"\s+", " ", text or "")

    return text.strip()


def fetch_page(url: str) -> tuple[str, int]:
    """Fetch an event page."""

    try:
        response = SESSION.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True,
        )

        return response.text, response.status_code

    except requests.RequestException as error:
        print(
            f"   ⚠️ Verification failed: "
            f"{url}"
        )
        print(
            f"      {error}"
        )

        return "", 0


def extract_page_text(
    html: str,
) -> tuple[str, str]:

    if not html:
        return "", ""

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # Remove elements that don't provide useful event evidence.
    for element in soup(
        ["script", "style", "noscript"]
    ):
        element.decompose()

    title = ""

    if soup.title:
        title = clean_text(
            soup.title.get_text(
                " ",
                strip=True,
            )
        )

    text = clean_text(
        soup.get_text(
            " ",
            strip=True,
        )
    )

    return title, text


def contains_registration_signal(
    text: str,
) -> bool:

    patterns = [
        "register",
        "registration",
        "rsvp",
        "book now",
        "tickets",
        "reserve your spot",
        "sign up",
        "join us",
    ]

    text_lower = text.lower()

    return any(
        pattern in text_lower
        for pattern in patterns
    )


def contains_date_signal(
    text: str,
) -> bool:

    patterns = [
        r"\b\d{1,2}\s+"
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
        r"[a-z]*\s+\d{4}\b",

        r"\b"
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
        r"[a-z]*\s+\d{1,2}"
        r"(?:,\s*|\s+)\d{4}\b",

        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",

        r"\b20\d{2}\b",
    ]

    text_lower = text.lower()

    return any(
        re.search(
            pattern,
            text_lower,
        )
        for pattern in patterns
    )


def contains_location_signal(
    text: str,
) -> bool:

    locations = [
        "hyderabad",
        "bengaluru",
        "bangalore",
        "mumbai",
        "pune",
        "chennai",
        "delhi",
        "noida",
        "gurugram",
        "gurgaon",
        "kolkata",
        "kochi",
        "ahmedabad",
        "jaipur",
        "chandigarh",
        "bhubaneswar",
        "lucknow",
        "indore",
        "coimbatore",
        "visakhapatnam",
        "india",
        "online",
        "virtual",
    ]

    text_lower = text.lower()

    return any(
        location in text_lower
        for location in locations
    )


def verify_event(
    url: str,
) -> VerificationResult:

    print()
    print(
        f"🔍 Verifying: {url}"
    )

    html, status_code = fetch_page(url)

    if not html or status_code < 200 or status_code >= 400:

        print(
            f"   ❌ Page unavailable "
            f"(HTTP {status_code})"
        )

        return VerificationResult(
            url=url,
            reachable=False,
            status_code=status_code,
            title="",
            text="",
            has_registration_signal=False,
            has_date_signal=False,
            has_location_signal=False,
            verified_at=datetime.now(
                timezone.utc
            ).isoformat(),
        )

    title, text = extract_page_text(
        html
    )

    registration = contains_registration_signal(
        text
    )

    date_signal = contains_date_signal(
        text
    )

    location_signal = contains_location_signal(
        text
    )

    print(
        f"   ✅ HTTP {status_code}"
    )

    print(
        f"   Title: {title[:120]}"
    )

    print(
        f"   Registration signal: "
        f"{registration}"
    )

    print(
        f"   Date signal: "
        f"{date_signal}"
    )

    print(
        f"   Location signal: "
        f"{location_signal}"
    )

    return VerificationResult(
        url=url,
        reachable=True,
        status_code=status_code,
        title=title,
        text=text,
        has_registration_signal=registration,
        has_date_signal=date_signal,
        has_location_signal=location_signal,
        verified_at=datetime.now(
            timezone.utc
        ).isoformat(),
    )


def verification_score(
    result: VerificationResult,
) -> int:

    score = 0

    if result.reachable:
        score += 40

    if result.has_date_signal:
        score += 25

    if result.has_location_signal:
        score += 20

    if result.has_registration_signal:
        score += 15

    return min(score, 100)


if __name__ == "__main__":

    print(
        "verifier.py is ready."
    )

    print(
        "It will be connected to the discovery "
        "pipeline in the next step."
    )
