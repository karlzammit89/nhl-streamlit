import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# TITLE
# =========================
st.title("🏒 NHL Dashboard")

mode = st.radio("Select Mode", ["Schedule", "Game Feed"])

BASE_URL = "https://statsapi.web.nhl.com/api/v1"

# =========================
# HELPERS
# =========================
def convert_to_et(raw_time):
    if raw_time:
        try:
            dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
            return dt.astimezone(ZoneInfo("America/New_York"))
        except:
            return None
    return None


def convert_to_et_str(raw_time):
    dt = convert_to_et(raw_time)
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    return None


def get_event_emoji(event):
    event = (event or "").lower()

    if "goal" in event:
        return "🥅"
    if "shot" in event:
        return "🎯"
    if "missed shot" in event:
        return "😬"
    if "blocked shot" in event:
        return "🧱"
    if "hit" in event:
        return "💥"
    if "penalty" in event:
        return "🚨"
    if "faceoff" in event:
        return "🎲"

    return "🏒"


# =========================
# MODE 1 — SCHEDULE
# =========================
if mode == "Schedule":

    date = st.text_input("Enter date (YYYY-MM-DD)", "2026-04-22")

    if st.button("Load Games"):

        url = f"{BASE_URL}/schedule?date={date}"
        data = requests.get(url).json()

        games = []

        for d in data.get("dates", []):
            for g in d.get("games", []):

                games.append({
                    "gamePk": g["gamePk"],
                    "matchup": f'{g["teams"]["away"]["team"]["name"]} @ {g["teams"]["home"]["team"]["name"]}',
                    "time": convert_to_et_str(g.get("gameDate"))
                })

        if games:
            for game in games:
                time_only = game["time"].split(" ")[1][:5] if game["time"] else "N/A"
                st.write(f"{game['gamePk']} | 🏒 {game['matchup']} | 🕒 {time_only} (ET)")
        else:
            st.warning("No games found")


# =========================
# MODE 2 — GAME FEED
# =========================
if mode == "Game Feed":

    game_pk = st.text_input("Enter Game ID", "")

    if st.button("Load Game Feed"):

        url = f"{BASE_URL}/game/{game_pk}/feed/live"
        data = requests.get(url).json()

        plays = data.get("liveData", {}).get("plays", {}).get("allPlays", [])

        if not plays:
            st.warning("No game data found")
            st.stop()

        st.subheader("🏒 Live Game Feed")

        prev_score = None

        for play in plays:

            event = play.get("result", {}).get("event")
            desc = play.get("result", {}).get("description")

            period = play.get("about", {}).get("period")
            period_time = play.get("about", {}).get("periodTime")

            away_score = play.get("result", {}).get("awayScore")
            home_score = play.get("result", {}).get("homeScore")

            score = f"{away_score} - {home_score}"

            emoji = get_event_emoji(event)

            st.subheader(f"{emoji} {event}")

            if score != prev_score and prev_score is not None:
                st.write(f"🏟️ Period {period} | 📊 {score} 🔥 GOAL EVENT 🔥")
            else:
                st.write(f"🏟️ Period {period} | 📊 {score}")

            st.write(f"📌 {desc}")
            st.write(f"⏱️ Time in Period: {period_time}")

            st.divider()

            prev_score = score

        st.success(f"Loaded {len(plays)} plays")
