from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from collectors import collect_candidates
from verifier import verify_event, verification_score
from telegram import send_event_alert


# ============================================================
# CONFIGURATION
# ============================================================

STATE_FILE = Path("sent_events.json")

# Maximum number of NEW Telegram alerts per run.
MAX_TELEGRAM_ALERTS_PER_RUN = 10

# India timezone
INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")


# ============================================================
# INDIA DATE
# ============================================================

def get_india_today() -> date:
    """Return today's date in India."""

    return datetime.now(
        INDIA_TIMEZONE
    ).date()


# ============================================================
# DATE PARSING
# ============================================================

def parse_pipeline_date(value: str) -> date | None:
    """
    Parse common date formats.

    This is an additional safety parser for pipeline.py.
    verifier.py remains the primary date parser.
    """

    if not isinstance(value, str):
        return None

    value = value.strip()

    formats = (
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%B %d %Y",
        "%b %d, %Y",
        "%b %d %Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
    )

    for fmt in formats:
        try:
            return datetime.strptime(
                value,
                fmt
            ).date()
        except ValueError:
            continue

    return None


# ============================================================
# STRICT TODAY FILTER
# ============================================================

def event_is_today(result) -> bool:
    """
    Return True only when the event is happening today
    in India.

    Rules:

    Today:
        ALLOW

    Tomorrow:
        REJECT

    Yesterday:
        REJECT

    Future:
        REJECT

    Unknown date:
        REJECT

    Multi-day event containing today:
        ALLOW
    """

    today = get_india_today()

    detected_dates = getattr(
        result,
        "detected_dates",
        None
    )

    if not detected_dates:
        return False

    parsed_dates = []

    for value in detected_dates:

        if isinstance(value, date):

            parsed_dates.append(value)

            continue

        parsed = parse_pipeline_date(
            value
        )

        if parsed:
            parsed_dates.append(parsed)

    if not parsed_dates:
        return False

    # Exact today match
    if today in parsed_dates:
        return True

    # Multi-day event protection
    earliest = min(parsed_dates)
    latest = max(parsed_dates)

    return (
        earliest
        <= today
        <= latest
    )


# ============================================================
# STATE MANAGEMENT
# ============================================================

def load_sent_urls() -> set[str]:
    """
    Load event URLs that were successfully sent
    to Telegram in previous runs.
    """

    if not STATE_FILE.exists():

        print(
            "ℹ️ sent_events.json not found."
        )

        return set()

    try:

        with STATE_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(
            data,
            dict
        ):

            print(
                "⚠️ Invalid state file format."
            )

            return set()

        sent_urls = data.get(
            "sent_urls",
            []
        )

        if not isinstance(
            sent_urls,
            list
        ):

            print(
                "⚠️ Invalid sent_urls format."
            )

            return set()

        return {
            str(url).strip()
            for url in sent_urls
            if str(url).strip()
        }

    except (
        json.JSONDecodeError,
        OSError,
    ) as exc:

        print(
            f"⚠️ Could not read "
            f"{STATE_FILE}: {exc}"
        )

        return set()


def save_sent_urls(
    sent_urls: set[str],
) -> bool:
    """
    Save URLs only after Telegram successfully
    sends the corresponding event.
    """

    try:

        data = {
            "sent_urls": sorted(
                sent_urls
            )
        }

        with STATE_FILE.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

        print(
            f"💾 Saved "
            f"{len(sent_urls)} "
            f"sent event URLs."
        )

        return True

    except OSError as exc:

        print(
            f"❌ Could not save "
            f"{STATE_FILE}: {exc}"
        )

        return False


# ============================================================
# SAFE VALUE HELPER
# ============================================================

def safe_value(
    value,
    default: str = "",
) -> str:
    """
    Safely convert an extracted value to text.
    """

    if value is None:
        return default

    value = str(value).strip()

    return value or default


# ============================================================
# BUILD EVENT OBJECT
# ============================================================

def build_verified_event(
    candidate,
    result,
    score: int,
    today: date,
) -> dict:
    """
    Convert the verifier result into the complete event
    object used by Telegram.
    """

    event_date = safe_value(
        getattr(
            result,
            "event_date",
            ""
        )
    )

    event_end_date = safe_value(
        getattr(
            result,
            "event_end_date",
            ""
        )
    )

    event_time = safe_value(
        getattr(
            result,
            "event_time",
            ""
        )
    )

    event_location = safe_value(
        getattr(
            result,
            "event_location",
            ""
        )
    )

    event_venue = safe_value(
        getattr(
            result,
            "event_venue",
            ""
        )
    )

    event_city = safe_value(
        getattr(
            result,
            "event_city",
            ""
        )
    )

    event_state = safe_value(
        getattr(
            result,
            "event_state",
            ""
        )
    )

    event_country = safe_value(
        getattr(
            result,
            "event_country",
            ""
        )
    )

    event_mode = safe_value(
        getattr(
            result,
            "event_mode",
            ""
        )
    )

    event_organizer = safe_value(
        getattr(
            result,
            "event_organizer",
            ""
        )
    )

    event_type = safe_value(
        getattr(
            result,
            "event_type",
            ""
        )
    )

    event_price = safe_value(
        getattr(
            result,
            "event_price",
            ""
        )
    )

    registration_url = safe_value(
        getattr(
            result,
            "registration_url",
            ""
        )
    )

    event_url = safe_value(
        getattr(
            result,
            "event_url",
            ""
        )
    )

    event_description = safe_value(
        getattr(
            result,
            "event_description",
            ""
        )
    )

    # Fallbacks
    if not event_url:
        event_url = safe_value(
            candidate.url
        )

    if not event_description:
        event_description = safe_value(
            candidate.description
        )

    if not event_date:

        event_date = today.isoformat()

    return {
        # ----------------------------------------------------
        # Basic event information
        # ----------------------------------------------------

        "title": safe_value(
            candidate.title
        ),

        "url": safe_value(
            candidate.url
        ),

        "source": safe_value(
            candidate.source
        ),

        "description": safe_value(
            candidate.description
        ),

        "page_title": safe_value(
            result.title
        ),

        # ----------------------------------------------------
        # Verification
        # ----------------------------------------------------

        "verification_score": score,

        "has_registration": (
            bool(
                result.has_registration_signal
            )
        ),

        "has_date": (
            bool(
                result.has_date_signal
            )
        ),

        "has_future_date": (
            bool(
                result.has_future_date
            )
        ),

        "has_location": (
            bool(
                result.has_location_signal
            )
        ),

        "has_india_location": (
            bool(
                result.has_india_location
            )
        ),

        "has_online_signal": (
            bool(
                result.has_online_signal
            )
        ),

        "detected_dates": (
            list(
                getattr(
                    result,
                    "detected_dates",
                    []
                )
            )
        ),

        # ----------------------------------------------------
        # Actual event details
        # ----------------------------------------------------

        "event_date": event_date,

        "event_end_date": event_end_date,

        "event_time": event_time,

        "event_location": event_location,

        "event_venue": event_venue,

        "event_city": event_city,

        "event_state": event_state,

        "event_country": event_country,

        "event_mode": event_mode,

        "event_organizer": event_organizer,

        "event_type": event_type,

        "event_price": event_price,

        # ----------------------------------------------------
        # URLs
        # ----------------------------------------------------

        "registration_url": (
            registration_url
        ),

        "event_url": event_url,

        # ----------------------------------------------------
        # Description
        # ----------------------------------------------------

        "event_description": (
            event_description
        ),

        # ----------------------------------------------------
        # Today flag
        # ----------------------------------------------------

        "is_today": True,
    }


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_pipeline():

    today = get_india_today()

    print("=" * 60)
    print(
        "🇮🇳 INDIA CYBERSECURITY EVENT PIPELINE"
    )
    print("=" * 60)

    print()

    print(
        f"📅 TODAY FILTER: "
        f"{today.strftime('%d %B %Y')}"
    )

    print(
        "🇮🇳 Timezone: Asia/Kolkata"
    )

    # ========================================================
    # LOAD STATE
    # ========================================================

    sent_urls = load_sent_urls()

    print()

    print(
        f"📚 Previously sent events: "
        f"{len(sent_urls)}"
    )

    # ========================================================
    # COLLECT
    # ========================================================

    print()

    print(
        "🔎 Collecting cybersecurity events..."
    )

    try:

        candidates = collect_candidates()

    except Exception as exc:

        print(
            f"❌ Candidate collection failed: "
            f"{exc}"
        )

        return []

    print()

    print(
        f"📦 Candidates collected: "
        f"{len(candidates)}"
    )

    # ========================================================
    # VERIFY
    # ========================================================

    verified = []

    non_today_rejected = 0
    unreachable_rejected = 0
    low_score_rejected = 0
    unknown_date_rejected = 0

    for number, candidate in enumerate(
        candidates,
        start=1,
    ):

        print()

        print(
            f"[{number}/{len(candidates)}]"
        )

        print(
            f"   🔎 {candidate.title}"
        )

        # ----------------------------------------------------
        # Verify page
        # ----------------------------------------------------

        try:

            result = verify_event(
                candidate.url
            )

        except Exception as exc:

            print(
                f"   ❌ Verification error: "
                f"{exc}"
            )

            continue

        # ----------------------------------------------------
        # Unreachable
        # ----------------------------------------------------

        if not result.reachable:

            print(
                "   ❌ Rejected: "
                "page unreachable"
            )

            unreachable_rejected += 1

            continue

        # ----------------------------------------------------
        # Score
        # ----------------------------------------------------

        try:

            score = verification_score(
                result
            )

        except Exception as exc:

            print(
                f"   ❌ Scoring error: "
                f"{exc}"
            )

            continue

        print(
            f"   🔎 Verification score: "
            f"{score}/100"
        )

        # ----------------------------------------------------
        # Low score
        # ----------------------------------------------------

        if score < 40:

            print(
                f"   ⚠️ Rejected: "
                f"low verification score "
                f"{score}/100"
            )

            low_score_rejected += 1

            continue

        # ----------------------------------------------------
        # Date information
        # ----------------------------------------------------

        detected_dates = getattr(
            result,
            "detected_dates",
            []
        )

        print(
            f"   📅 Detected dates: "
            f"{detected_dates}"
        )

        # ----------------------------------------------------
        # Unknown date
        # ----------------------------------------------------

        if not detected_dates:

            print(
                "   ⏭️ Rejected: "
                "event date unknown"
            )

            unknown_date_rejected += 1

            continue

        # ----------------------------------------------------
        # STRICT TODAY-ONLY FILTER
        # ----------------------------------------------------

        if not event_is_today(
            result
        ):

            print(
                "   ⏭️ Rejected: "
                "event is NOT happening today"
            )

            non_today_rejected += 1

            continue

        # ----------------------------------------------------
        # TODAY EVENT
        # ----------------------------------------------------

        print(
            "   ✅ Event is happening TODAY"
        )

        # ----------------------------------------------------
        # Build rich event
        # ----------------------------------------------------

        event = build_verified_event(
            candidate,
            result,
            score,
            today,
        )

        # ----------------------------------------------------
        # Debug extracted information
        # ----------------------------------------------------

        print(
            f"   📅 Date: "
            f"{event['event_date']}"
        )

        if event["event_end_date"]:

            print(
                f"   📅 End date: "
                f"{event['event_end_date']}"
            )

        if event["event_time"]:

            print(
                f"   🕐 Time: "
                f"{event['event_time']}"
            )

        if event["event_location"]:

            print(
                f"   📍 Location: "
                f"{event['event_location']}"
            )

        if event["event_venue"]:

            print(
                f"   🏢 Venue: "
                f"{event['event_venue']}"
            )

        if event["event_city"]:

            print(
                f"   🏙️ City: "
                f"{event['event_city']}"
            )

        if event["event_state"]:

            print(
                f"   🗺️ State: "
                f"{event['event_state']}"
            )

        if event["event_mode"]:

            print(
                f"   🌐 Mode: "
                f"{event['event_mode']}"
            )

        if event["event_organizer"]:

            print(
                f"   🏢 Organizer: "
                f"{event['event_organizer']}"
            )

        if event["event_type"]:

            print(
                f"   🎯 Type: "
                f"{event['event_type']}"
            )

        if event["event_price"]:

            print(
                f"   💰 Price: "
                f"{event['event_price']}"
            )

        if event["registration_url"]:

            print(
                "   🎟️ Registration URL found"
            )

        verified.append(
            event
        )

    # ========================================================
    # DEDUPLICATION
    # ========================================================

    unique_verified = []

    seen_urls = set()

    for event in verified:

        url = event["url"].strip()

        if not url:
            continue

        if url in seen_urls:

            print()

            print(
                f"⚠️ Duplicate removed: "
                f"{event['title']}"
            )

            continue

        seen_urls.add(url)

        unique_verified.append(
            event
        )

    verified = unique_verified

    # ========================================================
    # SORT
    # ========================================================

    verified.sort(
        key=lambda event: event[
            "verification_score"
        ],
        reverse=True,
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print("=" * 60)

    print(
        f"✅ VERIFIED TODAY EVENTS: "
        f"{len(verified)}"
    )

    print("=" * 60)

    print(
        f"⏭️ Non-today events rejected: "
        f"{non_today_rejected}"
    )

    print(
        f"❓ Unknown-date events rejected: "
        f"{unknown_date_rejected}"
    )

    print(
        f"🌐 Unreachable pages rejected: "
        f"{unreachable_rejected}"
    )

    print(
        f"⚠️ Low-score events rejected: "
        f"{low_score_rejected}"
    )

    # ========================================================
    # FIND NEW EVENTS
    # ========================================================

    new_events = []

    for event in verified:

        url = event["url"].strip()

        if url in sent_urls:

            print()

            print(
                f"↩️ Already sent: "
                f"{event['title']}"
            )

            continue

        new_events.append(
            event
        )

    print()

    print("=" * 60)

    print(
        f"🆕 NEW TODAY EVENTS: "
        f"{len(new_events)}"
    )

    print("=" * 60)

    # ========================================================
    # NO NEW EVENTS
    # ========================================================

    if not new_events:

        print()

        print(
            "ℹ️ No new TODAY "
            "cybersecurity events."
        )

        print(
            "ℹ️ No Telegram alerts needed."
        )

        return verified

    # ========================================================
    # LIMIT TELEGRAM ALERTS
    # ========================================================

    events_to_alert = new_events[
        :MAX_TELEGRAM_ALERTS_PER_RUN
    ]

    skipped_count = (
        len(new_events)
        - len(events_to_alert)
    )

    print()

    print(
        f"📨 New TODAY events available: "
        f"{len(new_events)}"
    )

    print(
        f"📨 Alerts allowed this run: "
        f"{MAX_TELEGRAM_ALERTS_PER_RUN}"
    )

    if skipped_count > 0:

        print(
            f"⏭️ Additional TODAY events "
            f"not sent this run: "
            f"{skipped_count}"
        )

    # ========================================================
    # SEND TELEGRAM
    # ========================================================

    print()

    print("=" * 60)

    print(
        "📨 SENDING TODAY'S "
        "TELEGRAM ALERTS"
    )

    print("=" * 60)

    successful_alerts = 0
    failed_alerts = 0

    for number, event in enumerate(
        events_to_alert,
        start=1,
    ):

        print()

        print(
            f"📨 Sending event "
            f"{number}/"
            f"{len(events_to_alert)}"
        )

        print(
            f"   📌 {event['title']}"
        )

        # ----------------------------------------------------
        # Final safety check
        # ----------------------------------------------------

        if not event.get(
            "is_today",
            False
        ):

            print(
                "   🛑 BLOCKED: "
                "event is not marked TODAY"
            )

            continue

        # ----------------------------------------------------
        # Final URL check
        # ----------------------------------------------------

        if not event.get(
            "url",
            ""
        ).strip():

            print(
                "   🛑 BLOCKED: "
                "event URL missing"
            )

            failed_alerts += 1

            continue

        # ----------------------------------------------------
        # Send
        # ----------------------------------------------------

        try:

            success = send_event_alert(
                event
            )

        except Exception as exc:

            print(
                f"   ❌ Telegram error: "
                f"{exc}"
            )

            success = False

        # ----------------------------------------------------
        # Successful send
        # ----------------------------------------------------

        if success:

            successful_alerts += 1

            sent_urls.add(
                event["url"].strip()
            )

            print(
                "   ✅ Telegram alert sent"
            )

            print(
                "   💾 Event marked as sent"
            )

        # ----------------------------------------------------
        # Failed send
        # ----------------------------------------------------

        else:

            failed_alerts += 1

            print(
                "   ⚠️ Telegram alert failed"
            )

            print(
                "   ℹ️ Event NOT marked as sent"
            )

    # ========================================================
    # SAVE STATE
    # ========================================================

    print()

    if save_sent_urls(
        sent_urls
    ):

        print(
            "✅ Sent-event state saved."
        )

    else:

        print(
            "⚠️ Sent-event state "
            "could not be saved."
        )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()

    print("=" * 60)

    print(
        "📊 TELEGRAM SUMMARY"
    )

    print("=" * 60)

    print(
        f"📅 Pipeline date: "
        f"{today.strftime('%d %B %Y')}"
    )

    print(
        "🇮🇳 Timezone: "
        "Asia/Kolkata"
    )

    print(
        f"🆕 New TODAY events found: "
        f"{len(new_events)}"
    )

    print(
        f"📨 Alerts attempted: "
        f"{len(events_to_alert)}"
    )

    print(
        f"✅ Alerts sent: "
        f"{successful_alerts}"
    )

    print(
        f"❌ Alerts failed: "
        f"{failed_alerts}"
    )

    print(
        f"⏭️ Non-TODAY events rejected: "
        f"{non_today_rejected}"
    )

    print(
        f"❓ Unknown-date events rejected: "
        f"{unknown_date_rejected}"
    )

    print(
        f"📚 Total recorded as sent: "
        f"{len(sent_urls)}"
    )

    print("=" * 60)

    return verified


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_pipeline()
