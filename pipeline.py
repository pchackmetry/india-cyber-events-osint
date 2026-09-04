from __future__ import annotations

import json
from pathlib import Path

from collectors import collect_candidates
from verifier import verify_event, verification_score
from telegram import send_event_alert


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

STATE_FILE = Path("sent_events.json")

# Maximum number of NEW Telegram alerts per run.
MAX_TELEGRAM_ALERTS_PER_RUN = 10


# ------------------------------------------------------------
# STATE MANAGEMENT
# ------------------------------------------------------------

def load_sent_urls() -> set[str]:
    """
    Load URLs that have already been successfully
    sent to Telegram.
    """

    if not STATE_FILE.exists():
        print(
            "ℹ️ sent_events.json not found."
        )

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

        if not isinstance(
            sent_urls,
            list,
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

    print("=" * 60)
    print(
        "🇮🇳 INDIA CYBERSECURITY EVENT PIPELINE"
    )
    print("=" * 60)

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
        # Store verified event
        # ----------------------------------------------------

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
        f"✅ VERIFIED UNIQUE EVENTS: "
        f"{len(verified)}"
    )
    print("=" * 60)

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
        f"🆕 NEW EVENTS: "
        f"{len(new_events)}"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # NO NEW EVENTS
    # --------------------------------------------------------

    if not new_events:

        print()
        print(
            "ℹ️ No new cybersecurity events."
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
        f"📨 New events available: "
        f"{len(new_events)}"
    )

    print(
        f"📨 Alerts allowed this run: "
        f"{MAX_TELEGRAM_ALERTS_PER_RUN}"
    )

    if skipped_count > 0:

        print(
            f"⏭️ New events waiting for "
            f"future runs: "
            f"{skipped_count}"
        )

    # --------------------------------------------------------
    # SEND TELEGRAM ALERTS
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        "📨 SENDING NEW TELEGRAM ALERTS"
    )
    print("=" * 60)

    successful_alerts = 0

    for number, event in enumerate(
        events_to_alert,
        start=1,
    ):

        print()

        print(
            f"📨 Sending new event "
            f"{number}/"
            f"{len(events_to_alert)}"
        )

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
        f"🆕 New events found: "
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
        f"⏭️ New events waiting: "
        f"{skipped_count}"
    )

    print(
        f"📚 Total recorded as sent: "
        f"{len(sent_urls)}"
    )

    return verified


# ------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------

if __name__ == "__main__":
    run_pipeline()

