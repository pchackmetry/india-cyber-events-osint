from __future__ import annotations

from collectors import collect_candidates
from verifier import verify_event, verification_score


def run_pipeline():
    print("=" * 60)
    print("🇮🇳 INDIA CYBERSECURITY EVENT PIPELINE")
    print("=" * 60)

    candidates = collect_candidates()

    print()
    print(f"📦 Candidates collected: {len(candidates)}")

    verified = []

    for number, candidate in enumerate(candidates, start=1):
        print()
        print(f"[{number}/{len(candidates)}]")

        result = verify_event(candidate.url)

        score = verification_score(result)

        if not result.reachable:
            print("   ❌ Rejected: page unreachable")
            continue

        if score < 40:
            print(
                f"   ⚠️ Low verification score: {score}/100"
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

    verified.sort(
        key=lambda event: event["verification_score"],
        reverse=True,
    )

    print()
    print("=" * 60)
    print(
        f"✅ VERIFIED EVENTS: {len(verified)}"
    )
    print("=" * 60)

    for number, event in enumerate(
        verified,
        start=1,
    ):
        print()
        print(
            f"{number}. {event['title']}"
        )
        print(
            f"   Source: {event['source']}"
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
            f"   URL: {event['url']}"
        )

    return verified


if __name__ == "__main__":
    run_pipeline()
