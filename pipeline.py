from __future__ import annotations

from collectors import collect_candidates
from verifier import verify_event, verification_score
from telegram import send_telegram


def build_telegram_message(verified: list[dict]) -> str:
    """
    Build a Telegram message containing verified cybersecurity events.
    """

    message = (
        "🇮🇳 CYBERSECURITY EVENTS\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    for number, event in enumerate(
        verified,
        start=1,
    ):
        message += (
            f"🔐 {number}. {event['title']}\n\n"
            f"🌐 Source: {event['source']}\n"
            f"✅ Verification: "
            f"{event['verification_score']}/100\n"
            f"📝 Registration signal: "
            f"{event['has_registration']}\n"
            f"📅 Date signal: "
            f"{event['has_date']}\n"
            f"📍 Location signal: "
            f"{event['has_location']}\n"
            f"🔗 {event['url']}\n\n"
        )

    return message


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

        if not result.reachable:
            print(
                "   ❌ Rejected: "
                "page unreachable"
            )
            continue

        if score < 40:
            print(
                f"   ⚠️ Low verification score: "
                f"{score}/100"
            )
            continue

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
                "has_location": (
                    result.has_location_signal
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
    # PRINT RESULTS
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
            f"   Location signal: "
            f"{event['has_location']}"
        )
        print(
            f"   URL: "
            f"{event['url']}"
        )

    # --------------------------------------------------------
    # TELEGRAM ALERT
    # --------------------------------------------------------

    if verified:

        print()
        print("=" * 60)
        print("📨 SENDING TELEGRAM ALERT")
        print("=" * 60)

        telegram_message = (
            build_telegram_message(
                verified
            )
        )

        send_telegram(
            telegram_message
        )

    else:

        print()
        print(
            "ℹ️ No verified events found."
        )
        print(
            "ℹ️ No Telegram alert sent."
        )

    return verified


if __name__ == "__main__":
    run_pipeline()
