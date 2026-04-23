import streamlit as st
import requests
from datetime import datetime, timezone

st.title("🏒 NHL Live Dashboard (Official CDN API)")

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
# TIME FORMATTER
# =========================
def format_timestamp(ts):
    if not ts:
        return "N/A"

    try:
        # NHL gives ISO timestamps like "2026-04-23T19:42:31Z"
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return ts


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

            # ⏱️ REAL TIMESTAMP (when play happened)
            timestamp = format_timestamp(p.get("timeUTC"))

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

            st.subheader(f"{emoji} {event}")

            if score != prev_score and prev_score is not None:
                st.write(f"🏟️ Period {period} | 📊 {score} 🔥 SCORE CHANGE 🔥")
            else:
                st.write(f"🏟️ Period {period} | 📊 {score}")

            st.write(f"🕒 Event Time: {timestamp}")
            st.write(f"📌 {desc}")

            st.divider()

            prev_score = score

        st.success(f"Loaded {len(plays)} plays")
