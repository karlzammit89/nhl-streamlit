import streamlit as st
import requests
from datetime import datetime, timezone

st.title("🏒 NHL Dashboard (Official CDN API)")

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
# GAME TIME (HOCKEY CLOCK)
# =========================
def get_event_time(play):
    time_in_period = play.get("timeInPeriod")
    period = play.get("periodDescriptor", {}).get("number")
    sort_order = play.get("sortOrder")

    if time_in_period:
        return f"⏱️ Period Time: {time_in_period}"

    if period and sort_order:
        return f"📊 Period {period} | Seq {sort_order}"

    return "⏱️ Time: N/A"


# =========================
# REAL-WORLD INGEST TIME
# =========================
def get_ingest_time():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


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

        st.subheader("🏒 Live Game Feed")

        prev_score = None

        for p in plays:

            event = p.get("typeDescKey", "")
            desc = p.get("desc", "")

            period = p.get("periodDescriptor", {}).get("number")

            away_score = p.get("awayScore")
            home_score = p.get("homeScore")

            score = f"{away_score} - {home_score}"

            # 🧠 hockey game clock time
            event_time = get_event_time(p)

            # 🕒 real ingestion timestamp (your system time)
            ingest_time = get_ingest_time()

            # emoji mapping
            emoji = "🏒"

            if "goal" in event.lower():
                emoji = "🥅"
            elif "shot" in event.lower():
                emoji = "🎯"
            elif "penalty" in event.lower():
                emoji = "🚨"
            elif "hit" in event.lower():
                emoji = "💥"
            elif "missed shot" in event.lower():
                emoji = "😬"

            st.subheader(f"{emoji} {event}")

            if score != prev_score and prev_score is not None:
                st.write(f"🏟️ Period {period} | 📊 {score} 🔥 SCORE CHANGE 🔥")
            else:
                st.write(f"🏟️ Period {period} | 📊 {score}")

            # OUTPUT TIMES
            st.write(event_time)
            st.write(f"🕒 Received by app: {ingest_time}")
            st.write(f"📌 {desc}")

            st.divider()

            prev_score = score

        st.success(f"Loaded {len(plays)} plays")
