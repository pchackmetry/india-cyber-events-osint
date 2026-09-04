from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

from collectors import collect_candidates
from verifier import verify_event, verification_score
from telegram import send_event_alert


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

STATE_FILE = Path("sent_events.json")

# Maximum number of NEW Telegram alerts per run.
MAX_TELEGRAM_ALERTS_PER_RUN = 10

# India timezone
INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")


# ------------------------------------------------------------
# TODAY FILTER
# ------------------------------------------------------------

def get_india_today() -> date:
    """
    Return today's date in India.
    """
    from datetime import datetime

    return datetime.now(INDIA_TIMEZONE).date()


def event_is_today(result) -> bool:
    """
    Return True only when the verified event is happening today.

    Supports:
    - Single date
    - Multi-day date ranges, provided verifier.py exposes
      detected_dates containing the event dates.

    Unknown dates are rejected.
    """

    today = get_india_today()

    detected_dates = getattr(result, "detected_dates", None)

    if not detected_dates:
        return False

    parsed_dates = []

    for value in detected_dates:
        if isinstance(value, date):
            parsed_dates.append(value)
            continue

        if isinstance(value, str):
            value = value.strip()

            # Try common ISO format first
            try:
                parsed_dates.append(date.fromisoformat(value))
                continue
            except ValueError:
                pass

            # Try common display formats
            formats = (
                "%d %B %Y",
                "%d %b %Y",
                "%B %d %Y",
                "%b %d %Y",
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%Y/%m/%d",
            )

            for fmt in formats:
                try:
                    parsed_dates.append(
                        __import__("datetime")
                        .datetime.strptime(value, fmt)
                        .date()
                    )
                    break
                except ValueError:
                    continue

    if not parsed_dates:
        return False

    # If the exact date is today
    if today in parsed_dates:
        return True

    # For multi-day events, if verifier provides two or more
    # dates, consider the range between the earliest and latest.
    earliest = min(parsed_dates)
    latest = max(parsed_dates)

    if earliest <= today <= latest:
        return True

    return False


# ------------------------------------------------------------
# STATE MANAGEMENT
# ------------------------------------------------------------

def load_sent_urls() -> set[str]:
    """
    Load URLs that have already been successfully
    sent to Telegram.
    """

    if not STATE_FILE.exists():
        print("ℹ️ sent_events.json not found.")
        return set()

    try:
        with STATE_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        sent_urls = data.get(
            "sent_urls",
            [],
        )

        if not isinstance(sent_urls, list):
            print("⚠️ Invalid sent_urls format.")
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
    Save successfully alerted event URLs.
    """

    try:

        data = {
            "sent_urls": sorted(
                sent_urls
            )
        }

        with STATE_FILE.open(
            "w",
            encoding="utf-8",
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


# ------------------------------------------------------------
# MAIN PIPELINE
# ------------------------------------------------------------

def run_pipeline():

    today = get_india_today()

    print("=" * 60)
    print("🇮🇳 INDIA CYBERSECURITY EVENT PIPELINE")
    print("=" * 60)

    print()
    print(
        f"📅 TODAY FILTER: "
        f"{today.strftime('%d %B %Y')}"
    )

    # --------------------------------------------------------
    # LOAD PREVIOUSLY SENT EVENTS
    # --------------------------------------------------------

    sent_urls = load_sent_urls()

    print()
    print(
        f"📚 Previously sent events: "
        f"{len(sent_urls)}"
    )

    # --------------------------------------------------------
    # COLLECT
    # --------------------------------------------------------

    candidates = collect_candidates()

    print()
    print(
        f"📦 Candidates collected: "
        f"{len(candidates)}"
    )

    # --------------------------------------------------------
    # VERIFY
    # --------------------------------------------------------

    verified = []

    today_events_rejected = 0

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

        result = verify_event(
            candidate.url
        )

        score = verification_score(
            result
        )

        # ----------------------------------------------------
        # Reject unreachable pages
        # ----------------------------------------------------

        if not result.reachable:

            print(
                "   ❌ Rejected: "
                "page unreachable"
            )

            continue

        # ----------------------------------------------------
        # Reject low verification scores
        # ----------------------------------------------------

        if score < 40:

            print(
                f"   ⚠️ Low verification score: "
                f"{score}/100"
            )

            continue

        # ----------------------------------------------------
        # STRICT TODAY-ONLY FILTER
        # ----------------------------------------------------

        if not event_is_today(result):

            detected_dates = getattr(
                result,
                "detected_dates",
                [],
            )

            print(
                "   ⏭️ Rejected: "
                "event is not happening today"
            )

            print(
                f"   📅 Detected dates: "
                f"{detected_dates}"
            )

            today_events_rejected += 1

            continue

        # ----------------------------------------------------
        # Store verified TODAY event
        # ----------------------------------------------------

        print(
            "   ✅ Event is happening TODAY"
        )

        verified.append(
            {
                "title": candidate.title,
                "url": candidate.url,
                "source": candidate.source,
                "description": candidate.description,
                "verification_score": score,
                "page_title": result.title,

                "has_registration": (
                    result.has_registration_signal
                ),

                "has_date": (
                    result.has_date_signal
                ),

                "has_future_date": (
                    result.has_future_date
                ),

                "has_location": (
                    result.has_location_signal
                ),

                "has_india_location": (
                    result.has_india_location
                ),

                "has_online_signal": (
                    result.has_online_signal
                ),

                "detected_dates": (
                    result.detected_dates
                ),

                # Explicitly store today's date
                "event_date": today.isoformat(),

                # Useful for Telegram
                "is_today": True,
            }
        )

    # --------------------------------------------------------
    # REMOVE DUPLICATES FROM CURRENT RUN
    # --------------------------------------------------------

    unique_verified = []

    seen_urls = set()

    for event in verified:

        url = event["url"].strip()

        if not url:
            continue

        if url in seen_urls:

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

    # --------------------------------------------------------
    # SORT BY VERIFICATION SCORE
    # --------------------------------------------------------

    verified.sort(
        key=lambda event: event[
            "verification_score"
        ],
        reverse=True,
    )

    # --------------------------------------------------------
    # PRINT SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        f"✅ VERIFIED TODAY EVENTS: "
        f"{len(verified)}"
    )
    print("=" * 60)

    print(
        f"⏭️ Non-today events rejected: "
        f"{today_events_rejected}"
    )

    # --------------------------------------------------------
    # FIND NEW EVENTS
    # --------------------------------------------------------

    new_events = []

    for event in verified:

        url = event["url"].strip()

        if url in sent_urls:

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

    # --------------------------------------------------------
    # NO NEW EVENTS
    # --------------------------------------------------------

    if not new_events:

        print()
        print(
            "ℹ️ No new TODAY cybersecurity events."
        )

        print(
            "ℹ️ No Telegram alerts needed."
        )

        return verified

    # --------------------------------------------------------
    # LIMIT ALERTS
    # --------------------------------------------------------

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
            f"⏭️ TODAY events waiting for "
            f"future runs: "
            f"{skipped_count}"
        )

    # --------------------------------------------------------
    # SEND TELEGRAM ALERTS
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        "📨 SENDING TODAY'S TELEGRAM ALERTS"
    )
    print("=" * 60)

    successful_alerts = 0

    for number, event in enumerate(
        events_to_alert,
        start=1,
    ):

        print()

        print(
            f"📨 Sending TODAY event "
            f"{number}/"
            f"{len(events_to_alert)}"
        )

        # Final safety check immediately before Telegram.
        if not event.get("is_today", False):

            print(
                f"🛑 BLOCKED: "
                f"{event['title']} "
                f"is not marked as TODAY."
            )

            continue

        success = send_event_alert(
            event
        )

        if success:

            successful_alerts += 1

            # ----------------------------------------------
            # IMPORTANT:
            # Only mark as sent AFTER Telegram succeeds.
            # ----------------------------------------------

            sent_urls.add(
                event["url"].strip()
            )

            print(
                f"💾 Marked as sent: "
                f"{event['title']}"
            )

        else:

            print(
                f"⚠️ NOT marked as sent: "
                f"{event['title']}"
            )

    # --------------------------------------------------------
    # SAVE STATE
    # --------------------------------------------------------

    print()

    if save_sent_urls(
        sent_urls
    ):

        print(
            "✅ Sent-event state saved."
        )

    else:

        print(
            "⚠️ Sent-event state could "
            "not be saved."
        )

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("📊 TELEGRAM SUMMARY")
    print("=" * 60)

    print(
        f"📅 Pipeline date: "
        f"{today.strftime('%d %B %Y')}"
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
        f"{len(events_to_alert) - successful_alerts}"
    )

    print(
        f"⏭️ Events rejected because "
        f"they are not TODAY: "
        f"{today_events_rejected}"
    )

    print(
        f"📚 Total recorded as sent: "
        f"{len(sent_urls)}"
    )

    print("=" * 60)

    return verified


# ------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------

if __name__ == "__main__":
    run_pipeline()
