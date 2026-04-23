import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

st.title("🏒 NHL Dashboard (Enhanced Event Timeline)")

BASE_URL = "https://api-web.nhle.com/v1"

mode = st.radio("Mode", ["Schedule", "Game Feed"])


# =========================
# SAFE REQUEST
# =========================
def safe_get(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


# =========================
# GAME START TIME
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
# CLOCK → SECONDS
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
# ESTIMATED EVENT TIME
# =========================
def estimate_event_time(game_start, period, time_in_period):
    elapsed = clock_to_seconds(period, time_in_period)

    if game_start is None or elapsed is None:
        return "N/A"

    return (game_start + timedelta(seconds=elapsed)).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


# =========================
# SCHEDULE
# =========================
if mode == "Schedule":

    date = st.text_input("Enter date (YYYY-MM-DD)", "2026-04-22")

    if st.button("Load Schedule"):

        url = f"{BASE_URL}/schedule/{date}"
        data = safe_get(url)

        if not data:
            st.stop()

        games = []

        for week in data.get("gameWeek", []):
            for g in week.get("games", []):

                game_id = g.get("id")

                away = g["awayTeam"]["placeName"]["default"]
                home = g["homeTeam"]["placeName"]["default"]

                games.append({
                    "id": game_id,
                    "matchup": f"{away} @ {home}",
                    "time": g.get("startTimeUTC"),
                    "status": g.get("gameState")
                })

        if not games:
            st.warning("No games found")
        else:
            for g in games:
                st.write(
                    f"🏒 {g['id']} | {g['matchup']} | 🕒 {g['time']} | {g['status']}"
                )


# =========================
# GAME FEED
# =========================
if mode == "Game Feed":

    game_id = st.text_input("Enter Game ID", "")

    if st.button("Load Game Feed"):

        url = f"{BASE_URL}/gamecenter/{game_id}/play-by-play"
        data = safe_get(url)

        if not data:
            st.stop()

        plays = data.get("plays", [])

        if not plays:
            st.warning("No live data found")
            st.stop()

        st.subheader("🏒 Live Game Feed (Reconstructed Timeline)")

        # GAME START
        game_start = parse_game_start(data)

        prev_score = None

        for p in plays:

            event_type = p.get("typeDescKey", "").lower()
            desc = p.get("desc", "")

            period = p.get("periodDescriptor", {}).get("number")
            time_in_period = p.get("timeInPeriod")

            away_score = p.get("awayScore")
            home_score = p.get("homeScore")

            score = f"{away_score} - {home_score}"

            # 🧠 reconstructed timestamp
            event_time = estimate_event_time(
                game_start,
                period,
                time_in_period
            )

            # emoji mapping
            emoji = "🏒"

            if "goal" in event_type:
                emoji = "🥅"
            elif "penalty" in event_type:
                emoji = "🚨"
            elif "shot" in event_type:
                emoji = "🎯"
            elif "hit" in event_type:
                emoji = "💥"

            st.subheader(f"{emoji} {event_type}")

            if score != prev_score and prev_score is not None:
                st.write(f"🏟️ Period {period} | 📊 {score} 🔥 SCORE CHANGE 🔥")
            else:
                st.write(f"🏟️ Period {period} | 📊 {score}")

            # TIMELINE OUTPUT
            st.write(f"🕒 Estimated Event Time: {event_time}")
            st.write(f"⏱️ Game Clock: {time_in_period}")
            st.write(f"📌 {desc}")

            st.divider()

            prev_score = score

        st.success(f"Loaded {len(plays)} plays")
