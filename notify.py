"""
notify.py - macOS push notifications for ElonWatch
Uses osascript (AppleScript) — zero dependencies, works on all macOS.
Falls back gracefully if notification fails.
"""

import subprocess
import logging

logger = logging.getLogger("elonwatch.notify")


def send_notification(
    title: str,
    message: str,
    subtitle: str = "",
    urgency: int = 5,
    sound: bool = True,
) -> None:
    """
    Send a macOS notification via osascript.
    Sound plays for high-urgency items (urgency >= 7).
    """
    # Sanitize: escape double quotes for AppleScript
    def _esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")

    t = _esc(title[:80])
    m = _esc(message[:200])
    sub = _esc(subtitle[:80]) if subtitle else ""

    # Pick sound based on urgency
    if urgency >= 9:
        snd = "Basso"
    elif urgency >= 7:
        snd = "Ping"
    else:
        snd = "Pop" if sound else ""

    # Build AppleScript
    sub_clause = f'subtitle "{sub}"' if sub else ""
    snd_clause = f'sound name "{snd}"' if snd else ""

    script = f'''
    display notification "{m}" with title "{t}" {sub_clause} {snd_clause}
    '''

    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5,
        )
        logger.info(f"[notify] sent: {title}")
    except subprocess.TimeoutExpired:
        logger.warning("[notify] osascript timed out")
    except Exception as e:
        logger.warning(f"[notify] failed: {e}")


def test_notification() -> None:
    send_notification(
        title="ELONWATCH // FUTURE SYNC",
        subtitle="System Online",
        message="Consciousness feed is active. Signal monitoring engaged.",
        urgency=5,
    )


if __name__ == "__main__":
    test_notification()
    print("Notification sent.")
