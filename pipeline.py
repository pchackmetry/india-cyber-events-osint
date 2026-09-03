from __future__ import annotations

from collectors import collect_candidates
from verifier import verify_event, verification_score
from telegram import send_event_alert


def run_pipeline():
    print("=" * 60)
    print("🇮🇳 INDIA CYBERSECURITY EVENT PIPELINE")
    print("=" * 60)

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
    # SORT BY VERIFICATION SCORE
    # --------------------------------------------------------

    verified.sort(
        key=lambda event: event[
            "verification_score"
        ],
        reverse=True,
    )

    # --------------------------------------------------------
    # PRINT VERIFIED EVENTS
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        f"✅ VERIFIED EVENTS: "
        f"{len(verified)}"
    )
    print("=" * 60)

    for number, event in enumerate(
        verified,
        start=1,
    ):
        print()

        print(
            f"{number}. "
            f"{event['title']}"
        )

        print(
            f"   Source: "
            f"{event['source']}"
        )

        print(
            f"   Verification: "
            f"{event['verification_score']}/100"
        )

        print(
            f"   Registration: "
            f"{event['has_registration']}"
        )

        print(
            f"   Date signal: "
            f"{event['has_date']}"
        )

        print(
            f"   Future date: "
            f"{event['has_future_date']}"
        )

        print(
            f"   Location signal: "
            f"{event['has_location']}"
        )

        print(
            f"   India location: "
            f"{event['has_india_location']}"
        )

        print(
            f"   Online signal: "
            f"{event['has_online_signal']}"
        )

        print(
            f"   Detected dates: "
            f"{event['detected_dates']}"
        )

        print(
            f"   URL: "
            f"{event['url']}"
        )

    # --------------------------------------------------------
    # TELEGRAM ALERTS
    # --------------------------------------------------------

    if verified:

        print()
        print("=" * 60)
        print(
            "📨 SENDING INDIVIDUAL TELEGRAM ALERTS"
        )
        print("=" * 60)

        successful_alerts = 0

        for number, event in enumerate(
            verified,
            start=1,
        ):

            print()
            print(
                f"📨 Sending event "
                f"{number}/{len(verified)}"
            )

            success = send_event_alert(
                event
            )

            if success:
                successful_alerts += 1

        print()
        print(
            f"📨 Telegram alerts sent: "
            f"{successful_alerts}/"
            f"{len(verified)}"
        )

    else:

        print()
        print(
            "ℹ️ No verified events found."
        )

        print(
            "ℹ️ No Telegram alerts sent."
        )

    return verified


if __name__ == "__main__":
    run_pipeline()
