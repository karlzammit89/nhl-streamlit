import streamlit as st
import requests
from datetime import datetime

st.title("🏒 NHL Live Dashboard (Official CDN API)")

BASE_URL = "https://api-web.nhle.com/v1"

mode = st.radio("Mode", ["Schedule", "Game Feed"])

# =========================
# SAFE REQUEST WRAPPER
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
                st.write(f"🏒 {g['id']} | {g['matchup']} | 🕒 {g['time']} | {g['status']}")


# =========================
# GAME FEED
# =========================
if mode == "Game Feed":

    game_id = st.text_input("Enter Game ID", "")

    auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)

    if st.button("Load Game") or auto_refresh:

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

            # simple emoji system
            emoji = "🏒"

            if "goal" in event.lower():
                emoji = "🥅"
            elif "shot" in event.lower():
                emoji = "🎯"
            elif "penalty" in event.lower():
                emoji = "🚨"

            st.subheader(f"{emoji} {event}")

            if score != prev_score and prev_score is not None:
                st.write(f"🏟️ Period {period} | 📊 {score} 🔥 SCORE CHANGE 🔥")
            else:
                st.write(f"🏟️ Period {period} | 📊 {score}")

            st.write(f"📌 {desc}")
            st.divider()

            prev_score = score

        st.success(f"Loaded {len(plays)} plays")

        # simple auto refresh loop (Streamlit-safe hack)
        if auto_refresh:
            st.rerun()
