from datetime import datetime, timedelta


# =========================
# GAME START PARSER
# =========================
def parse_game_start(game_data):
    ts = (
        game_data.get("gameData", {})
        .get("datetime", {})
        .get("dateTime")
    )

    if not ts:
        return None

    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


# =========================
# CONVERT GAME CLOCK → ELAPSED SECONDS
# =========================
def clock_to_seconds(period, time_in_period):
    if not period or not time_in_period:
        return None

    try:
        minutes, seconds = map(int, time_in_period.split(":"))
    except:
        return None

    period_offset = (period - 1) * 20 * 60
    remaining_in_period = (20 * 60) - (minutes * 60 + seconds)

    return period_offset + remaining_in_period


# =========================
# MAIN "FAKE BUT CONSISTENT" TIMESTAMP
# =========================
def estimate_event_time(game_start, period, time_in_period):
    elapsed = clock_to_seconds(period, time_in_period)

    if game_start is None or elapsed is None:
        return "N/A"

    return (game_start + timedelta(seconds=elapsed)).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )
