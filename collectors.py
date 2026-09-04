from __future__ import annotations

import re
import requests

from bs4 import BeautifulSoup
from dataclasses import dataclass
from urllib.parse import quote, urljoin, urlparse, parse_qs, urlencode


# ============================================================
# CONFIGURATION
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}

TIMEOUT = 20


# ============================================================
# CANDIDATE MODEL
# ============================================================

@dataclass
class Candidate:
    title: str
    url: str
    source: str
    description: str = ""


# ============================================================
# INDIAN LOCATIONS
# ============================================================

INDIAN_CITIES = [
    "Hyderabad",
    "Bengaluru",
    "Bangalore",
    "Mumbai",
    "Pune",
    "Chennai",
    "Delhi",
    "New Delhi",
    "Gurugram",
    "Gurgaon",
    "Noida",
    "Kolkata",
    "Kochi",
    "Ahmedabad",
    "Jaipur",
    "Chandigarh",
    "Bhubaneswar",
    "Lucknow",
    "Indore",
    "Coimbatore",
    "Visakhapatnam",
    "Vijayawada",
    "Thiruvananthapuram",
    "Mysuru",
    "Mysore",
    "Nagpur",
    "Surat",
    "Vadodara",
    "Goa",
]


INDIAN_STATES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Delhi",
]


# ============================================================
# FOREIGN LOCATION SIGNALS
# ============================================================

FOREIGN_LOCATIONS = [
    "united states",
    "usa",
    "u.s.a",
    "u.s.",
    "canada",
    "united kingdom",
    "uk",
    "england",
    "scotland",
    "australia",
    "new zealand",
    "germany",
    "france",
    "spain",
    "italy",
    "netherlands",
    "ireland",
    "singapore",
    "malaysia",
    "indonesia",
    "philippines",
    "japan",
    "south korea",
    "korea",
    "china",
    "brazil",
    "mexico",
    "poland",
    "sweden",
    "norway",
    "denmark",
    "switzerland",
    "israel",
    "uae",
    "dubai",
    "abu dhabi",
]


FOREIGN_CITY_SIGNALS = [
    "raleigh",
    "durham",
    "charlotte",
    "new york",
    "los angeles",
    "san francisco",
    "seattle",
    "boston",
    "chicago",
    "austin",
    "dallas",
    "houston",
    "washington dc",
    "washington, dc",
    "atlanta",
    "denver",
    "miami",
    "toronto",
    "vancouver",
    "london",
    "manchester",
    "sydney",
    "melbourne",
    "berlin",
    "paris",
    "amsterdam",
    "singapore",
]


# ============================================================
# CYBERSECURITY TOPICS
# ============================================================

CYBER_TOPICS = [
    "cybersecurity",
    "cyber security",
    "information security",
    "infosec",
    "application security",
    "appsec",
    "cloud security",
    "ai security",
    "network security",
    "soc",
    "blue team",
    "red team",
    "penetration testing",
    "pentesting",
    "ethical hacking",
    "vapt",
    "vulnerability",
    "bug bounty",
    "digital forensics",
    "dfir",
    "incident response",
    "threat intelligence",
    "malware",
    "osint",
    "grc",
    "iam",
    "identity security",
    "ctf",
    "capture the flag",
    "owasp",
    "zero trust",
    "ransomware",
    "devsecops",
    "security operations",
    "cyber crime",
    "cybercrime",
    "digital security",
    "privacy engineering",
]


# ============================================================
# EVENT TYPES
# ============================================================

EVENT_TYPES = [
    "event",
    "meetup",
    "conference",
    "workshop",
    "webinar",
    "summit",
    "training",
    "seminar",
    "networking",
    "community",
    "ctf",
    "hackathon",
    "talk",
    "session",
    "bootcamp",
]


# ============================================================
# INVALID / NON-EVENT LINK SIGNALS
# ============================================================

INVALID_LINK_TEXT = {
    "global events",
    "regional events",
    "partner events",
    "all events",
    "upcoming events",
    "past events",
    "event calendar",
    "events calendar",
    "event listings",
    "events listings",
    "events directory",
    "event directory",
    "event archive",
    "events archive",
    "chapters",
    "all chapters",
    "find events",
    "browse events",
    "view all events",
    "see all events",
    "discover events",
    "discover",
    "event search",
    "search events",
    "sign in",
    "login",
    "register",
    "sign up",
}


INVALID_FRAGMENT_NAMES = {
    "#global",
    "#partner",
    "#partners",
    "#regional",
    "#regional-events",
    "#global-events",
    "#upcoming",
    "#past",
    "#events",
    "#calendar",
}


# ============================================================
# PUBLIC DIRECT SOURCES
# ============================================================

DIRECT_SOURCES = [
    {
        "name": "OWASP Events",
        "url": "https://owasp.org/events/",
    },
    {
        "name": "OWASP Chapters",
        "url": "https://owasp.org/chapters/",
    },
    {
        "name": "Null Community",
        "url": "https://null.community/",
    },
    {
        "name": "BSides",
        "url": "https://www.securitybsides.com/",
    },
]


# ============================================================
# FETCH
# ============================================================

def fetch(url: str) -> str | None:
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True,
        )

        print(
            f"   HTTP {response.status_code} | "
            f"{len(response.content)} bytes"
        )

        if response.status_code != 200:
            return None

        return response.text

    except requests.RequestException as exc:
        print(f"   ❌ Request error: {exc}")
        return None

    except Exception as exc:
        print(f"   ❌ Unexpected error: {exc}")
        return None


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ============================================================
# URL CLEANING
# ============================================================

def clean_url(url: str) -> str:
    """
    Safely normalize URLs.

    IMPORTANT:
    Do NOT globally unquote the complete URL.
    Query strings can contain encoded '&', '?', '/', etc.
    Decoding the entire URL can corrupt the URL.

    Only decode the specific Meetup returnUri parameter.
    """

    if not url:
        return ""

    url = url.strip()

    try:
        parsed = urlparse(url)

        # Remove fragment.
        fragment_removed = parsed._replace(fragment="")

        host = fragment_removed.netloc.lower()
        path = fragment_removed.path

        # --------------------------------------------------------
        # Meetup registration redirect
        # --------------------------------------------------------

        if (
            "meetup.com" in host
            and path.rstrip("/").lower() == "/register"
        ):
            query = parse_qs(
                fragment_removed.query,
                keep_blank_values=True,
            )

            return_values = query.get("returnUri", [])

            if return_values:
                target = return_values[0]

                target_parsed = urlparse(target)

                if (
                    "meetup.com" in target_parsed.netloc.lower()
                    and "/events/" in target_parsed.path.lower()
                ):
                    cleaned_target = (
                        "https://www.meetup.com"
                        f"{target_parsed.path}"
                    )

                    useful_query = {}

                    target_query = parse_qs(
                        target_parsed.query,
                        keep_blank_values=True,
                    )

                    for key in (
                        "eventorigin",
                        "recId",
                        "recSource",
                    ):
                        if key in target_query:
                            useful_query[key] = target_query[key]

                    if useful_query:
                        cleaned_target += (
                            "?"
                            + urlencode(
                                useful_query,
                                doseq=True,
                            )
                        )

                    print(
                        "      🔄 Meetup registration redirect -> "
                        f"{cleaned_target}"
                    )

                    return cleaned_target

        return fragment_removed.geturl().strip()

    except Exception:
        return url.split("#", 1)[0].strip()


# ============================================================
# MEETUP REDIRECT DETECTION
# ============================================================

def resolve_meetup_registration_url(url: str) -> str:
    cleaned = clean_url(url)

    if cleaned != url:
        return cleaned

    return url


# ============================================================
# INDIA LOCATION DETECTION
# ============================================================

def has_india_signal(text: str) -> bool:
    normalized = normalize(text)

    if re.search(r"\bindia\b", normalized):
        return True

    for city in INDIAN_CITIES:
        if re.search(
            rf"\b{re.escape(city.lower())}\b",
            normalized,
        ):
            return True

    for state in INDIAN_STATES:
        if re.search(
            rf"\b{re.escape(state.lower())}\b",
            normalized,
        ):
            return True

    return False


def has_foreign_signal(text: str) -> bool:
    normalized = normalize(text)

    for location in FOREIGN_LOCATIONS:
        if re.search(
            rf"\b{re.escape(location.lower())}\b",
            normalized,
        ):
            return True

    for city in FOREIGN_CITY_SIGNALS:
        if re.search(
            rf"\b{re.escape(city.lower())}\b",
            normalized,
        ):
            return True

    return False


def india_relevance(
    title: str,
    context: str,
    url: str,
) -> bool:
    """
    Conservative India filter.

    Physical events:
        Must contain a recognizable India signal.

    Online events:
        Allowed only when India is explicitly mentioned,
        OR when the search query itself strongly targets India.

    Foreign physical events are rejected.
    """

    combined = normalize(
        f"{title} {context} {url}"
    )

    india = has_india_signal(combined)
    foreign = has_foreign_signal(combined)

    # Explicit foreign location with no India signal.
    if foreign and not india:
        return False

    # India explicitly mentioned.
    if india:
        return True

    # Do not assume an arbitrary online event is Indian.
    return False


# ============================================================
# INVALID LINK DETECTION
# ============================================================

def is_invalid_link(
    title: str,
    url: str,
) -> bool:

    clean_title = normalize(title)
    clean_url_value = clean_url(url).lower()

    if not clean_url_value:
        return True

    try:
        parsed = urlparse(clean_url_value)

        # Meetup login/register/signin.
        if (
            "meetup.com" in parsed.netloc
            and parsed.path.rstrip("/").lower()
            in {
                "/register",
                "/login",
                "/signin",
                "/signup",
            }
        ):
            return True

    except Exception:
        pass

    # Fragment-only listing links.
    if "#" in clean_url_value:
        fragment = "#" + clean_url_value.split(
            "#",
            1,
        )[1]

        if fragment in INVALID_FRAGMENT_NAMES:
            return True

    if clean_title in INVALID_LINK_TEXT:
        return True

    listing_patterns = [
        r"/events/?$",
        r"/event/$",
        r"/search",
        r"/discover/?$",
        r"/calendar/?$",
        r"/categories/?$",
        r"/archive/?$",
        r"/directory/?$",
        r"/chapters/?$",
        r"/find/?$",
    ]

    for pattern in listing_patterns:
        if re.search(
            pattern,
            clean_url_value,
            flags=re.IGNORECASE,
        ):
            return True

    return False


# ============================================================
# CYBER RELEVANCE
# ============================================================

def is_cyber_event(
    title: str,
    context: str = "",
) -> bool:

    text = normalize(
        f"{title} {context}"
    )

    has_cyber = any(
        topic.lower() in text
        for topic in CYBER_TOPICS
    )

    has_event = any(
        event.lower() in text
        for event in EVENT_TYPES
    )

    return (
        has_cyber
        and has_event
    )


# ============================================================
# LOCATION DETECTION
# ============================================================

def detect_location(
    text: str,
) -> str:

    normalized = normalize(text)

    for city in INDIAN_CITIES:

        if re.search(
            rf"\b{re.escape(city.lower())}\b",
            normalized,
        ):
            if city.lower() == "bangalore":
                return "Bengaluru"

            if city.lower() == "mysore":
                return "Mysuru"

            return city

    for state in INDIAN_STATES:

        if re.search(
            rf"\b{re.escape(state.lower())}\b",
            normalized,
        ):
            return state

    if re.search(
        r"\bindia\b",
        normalized,
    ):
        return "India"

    if re.search(
        r"\bonline\b|\bvirtual\b",
        normalized,
    ):
        return "Online"

    return "Unknown"


# ============================================================
# PLATFORM EVENT URL VALIDATION
# ============================================================

def is_real_event_url(
    url: str,
) -> bool:

    try:
        parsed = urlparse(url)

        host = parsed.netloc.lower()
        path = parsed.path.lower()

        # ----------------------------------------------------
        # Meetup
        # ----------------------------------------------------

        if "meetup.com" in host:

            return bool(
                re.search(
                    r"/events/\d+",
                    path,
                )
            )

        # ----------------------------------------------------
        # Luma
        # ----------------------------------------------------

        if "lu.ma" in host:

            if path.rstrip("/") in {
                "",
                "/discover",
                "/search",
                "/signin",
                "/login",
            }:
                return False

            return True

        # ----------------------------------------------------
        # Eventbrite
        # ----------------------------------------------------

        if "eventbrite." in host:

            return bool(
                re.search(
                    r"/e/[^/]+",
                    path,
                )
            )

    except Exception:
        return False

    return True


# ============================================================
# SOURCE LINK EXTRACTION
# ============================================================

def extract_links(
    html: str,
    base_url: str,
    source_name: str,
) -> list[Candidate]:

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    candidates = []

    normalized_base = (
        clean_url(base_url)
        .split("#", 1)[0]
        .rstrip("/")
        .lower()
    )

    seen_urls = set()

    for link in soup.find_all(
        "a",
        href=True,
    ):

        title = link.get_text(
            " ",
            strip=True,
        )

        href = link.get(
            "href",
            "",
        ).strip()

        if not title:
            continue

        if not href:
            continue

        url = urljoin(
            base_url,
            href,
        )

        if not url.startswith("http"):
            continue

        # ----------------------------------------------------
        # Meetup redirect conversion.
        # ----------------------------------------------------

        original_url = url

        url = resolve_meetup_registration_url(
            url
        )

        if url != original_url:
            print(
                f"      🔄 Converted redirect: "
                f"{original_url} -> {url}"
            )

        # ----------------------------------------------------
        # Invalid/listing links.
        # ----------------------------------------------------

        if is_invalid_link(
            title,
            url,
        ):
            continue

        # ----------------------------------------------------
        # Platform-specific URL validation.
        # ----------------------------------------------------

        if source_name in {
            "Meetup",
            "Luma",
            "Eventbrite",
        }:

            if not is_real_event_url(
                url
            ):
                continue

        normalized_url = (
            clean_url(url)
            .split("#", 1)[0]
            .rstrip("/")
            .lower()
        )

        if normalized_url == normalized_base:
            continue

        if normalized_url in seen_urls:
            continue

        seen_urls.add(
            normalized_url
        )

        # ----------------------------------------------------
        # Nearby page context.
        # ----------------------------------------------------

        parent_text = ""

        parent = link.parent

        if parent:
            parent_text = parent.get_text(
                " ",
                strip=True,
            )

        container_text = ""

        for parent_level in (
            link.parent,
            (
                link.parent.parent
                if link.parent
                else None
            ),
        ):

            if parent_level:

                text = parent_level.get_text(
                    " ",
                    strip=True,
                )

                if len(text) > len(
                    container_text
                ):
                    container_text = text

        if len(container_text) > len(
            parent_text
        ):
            parent_text = container_text

        context = (
            f"{title} "
            f"{parent_text} "
            f"{url}"
        )

        # ----------------------------------------------------
        # Cybersecurity relevance.
        # ----------------------------------------------------

        if not is_cyber_event(
            title,
            context,
        ):
            continue

        # ----------------------------------------------------
        # INDIA FILTER.
        # ----------------------------------------------------

        if not india_relevance(
            title,
            context,
            url,
        ):
            print(
                f"      🌍 Skipping non-India event: "
                f"{title}"
            )
            continue

        location = detect_location(
            context
        )

        description = (
            f"Location signal: {location}"
        )

        candidates.append(
            Candidate(
                title=title,
                url=url,
                source=source_name,
                description=description,
            )
        )

    return candidates


# ============================================================
# DIRECT SOURCE COLLECTION
# ============================================================

def collect_direct_sources() -> list[Candidate]:

    print()
    print("=" * 60)
    print("🌐 DIRECT PUBLIC EVENT SOURCES")
    print("=" * 60)

    candidates = []

    for source in DIRECT_SOURCES:

        print()
        print(
            f"🔎 {source['name']}"
        )

        print(
            f"   {source['url']}"
        )

        html = fetch(
            source["url"]
        )

        if not html:
            print(
                "   ❌ Could not access source"
            )
            continue

        source_candidates = extract_links(
            html=html,
            base_url=source["url"],
            source_name=source["name"],
        )

        print(
            f"   Candidates: "
            f"{len(source_candidates)}"
        )

        candidates.extend(
            source_candidates
        )

    return candidates


# ============================================================
# SEARCH PAGES
# ============================================================

SEARCH_TEMPLATES = [
    (
        "Eventbrite",
        "https://www.eventbrite.com/d/india/{query}/",
    ),
    (
        "Meetup",
        "https://www.meetup.com/find/?keywords={query}&source=EVENTS",
    ),
    (
        "Luma",
        "https://lu.ma/discover?q={query}",
    ),
]


# ============================================================
# SEARCH QUERIES
# ============================================================

def build_search_queries() -> list[str]:

    queries = []

    # --------------------------------------------------------
    # India + topic
    # --------------------------------------------------------

    for topic in CYBER_TOPICS:

        queries.append(
            f"{topic} India event"
        )

    # --------------------------------------------------------
    # City + cybersecurity
    # --------------------------------------------------------

    for city in INDIAN_CITIES:

        queries.append(
            f"cybersecurity {city}"
        )

        queries.append(
            f"cyber security {city} meetup"
        )

        queries.append(
            f"infosec {city} event"
        )

        queries.append(
            f"security conference {city}"
        )

        queries.append(
            f"security workshop {city}"
        )

        queries.append(
            f"CTF {city}"
        )

        queries.append(
            f"cybersecurity networking {city}"
        )

    # --------------------------------------------------------
    # Community combinations
    # --------------------------------------------------------

    for city in INDIAN_CITIES:

        queries.append(
            f"OWASP {city}"
        )

        queries.append(
            f"Null security {city}"
        )

        queries.append(
            f"BSides {city}"
        )

    return list(
        dict.fromkeys(
            queries
        )
    )


# ============================================================
# SEARCH PAGE COLLECTION
# ============================================================

def collect_search_pages() -> list[Candidate]:

    print()
    print("=" * 60)
    print("🔎 CITY + TOPIC EVENT DISCOVERY")
    print("=" * 60)

    queries = build_search_queries()

    print(
        f"📋 Discovery queries: "
        f"{len(queries)}"
    )

    candidates = []

    # Keep this at 20 for the diagnostic run.
    max_queries = 20

    for number, query in enumerate(
        queries[:max_queries],
        start=1,
    ):

        print()
        print(
            f"[{number}/{min(len(queries), max_queries)}] "
            f"{query}"
        )

        encoded_query = quote(
            query,
            safe="",
        )

        for source_name, template in (
            SEARCH_TEMPLATES
        ):

            search_url = template.format(
                query=encoded_query
            )

            print(
                f"   → {source_name}"
            )

            html = fetch(
                search_url
            )

            if not html:
                continue

            source_candidates = extract_links(
                html=html,
                base_url=search_url,
                source_name=source_name,
            )

            if source_candidates:

                print(
                    f"      Found: "
                    f"{len(source_candidates)}"
                )

                candidates.extend(
                    source_candidates
                )

    return candidates


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate(
    candidates: list[Candidate],
) -> list[Candidate]:

    unique = {}

    for candidate in candidates:

        url = clean_url(
            candidate.url
        )

        url = url.split(
            "#",
            1,
        )[0]

        url = url.rstrip("/")

        if not url:
            continue

        if is_invalid_link(
            candidate.title,
            url,
        ):
            continue

        # ----------------------------------------------------
        # Final India safety check.
        # ----------------------------------------------------

        if not india_relevance(
            candidate.title,
            candidate.description,
            url,
        ):
            continue

        try:

            parsed = urlparse(
                url
            )

            if (
                "meetup.com"
                in parsed.netloc.lower()
                and parsed.path.rstrip("/").lower()
                in {
                    "/register",
                    "/login",
                    "/signin",
                    "/signup",
                }
            ):
                continue

        except Exception:
            continue

        if url not in unique:

            unique[url] = Candidate(
                title=candidate.title.strip(),
                url=url,
                source=candidate.source,
                description=candidate.description,
            )

    return list(
        unique.values()
    )


# ============================================================
# MAIN COLLECTOR
# ============================================================

def collect_candidates() -> list[Candidate]:

    print("=" * 60)
    print("🇮🇳 INDIA CYBERSECURITY EVENT DISCOVERY")
    print("=" * 60)

    all_candidates = []

    # --------------------------------------------------------
    # 1. Direct community sources
    # --------------------------------------------------------

    direct_candidates = (
        collect_direct_sources()
    )

    all_candidates.extend(
        direct_candidates
    )

    # --------------------------------------------------------
    # 2. Search discovery
    # --------------------------------------------------------

    search_candidates = (
        collect_search_pages()
    )

    all_candidates.extend(
        search_candidates
    )

    # --------------------------------------------------------
    # 3. Deduplicate
    # --------------------------------------------------------

    candidates = deduplicate(
        all_candidates
    )

    # --------------------------------------------------------
    # 4. Final report
    # --------------------------------------------------------

    print()
    print("=" * 60)

    print(
        f"📦 RAW CANDIDATES: "
        f"{len(all_candidates)}"
    )

    print(
        f"🇮🇳 INDIA CANDIDATES: "
        f"{len(candidates)}"
    )

    print("=" * 60)

    for number, candidate in enumerate(
        candidates[:50],
        start=1,
    ):

        print()

        print(
            f"[{number}] "
            f"{candidate.title}"
        )

        print(
            f"    Source: "
            f"{candidate.source}"
        )

        print(
            f"    {candidate.description}"
        )

        print(
            f"    URL: "
            f"{candidate.url}"
        )

    if len(candidates) > 50:

        print()

        print(
            f"... and "
            f"{len(candidates) - 50} "
            f"additional candidates."
        )

    return candidates


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":
    collect_candidates()
