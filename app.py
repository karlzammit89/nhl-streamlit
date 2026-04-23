import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# TITLE
# =========================
st.title("🏒 NHL Dashboard")

# =========================
# MODE (same as MLB style)
# =========================
mode = st.radio("Select Mode", ["Schedule"])

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


# =========================
# MODE 1 — SCHEDULE (MLB STYLE)
# =========================
if mode == "Schedule":

    date = st.text_input("Enter date (YYYY-MM-DD)", "2026-04-20")

    if st.button("Load Games"):

        url = f"https://api-web.nhle.com/v1/schedule/{date}"
        data = requests.get(url).json()

        games = []

        # =========================
        # PARSE GAMES (FULL DAY SEARCH)
        # =========================
        for week in data.get("gameWeek", []):
            for g in week.get("games", []):

                game_pk = g.get("id")

                away = g.get("awayTeam", {}).get("abbrev")
                home = g.get("homeTeam", {}).get("abbrev")

                start = g.get("startTimeUTC")
                state = g.get("gameState")

                et_time = convert_to_et_str(start)

                if et_time:
                    games.append({
                        "gamePk": game_pk,
                        "matchup": f"{away} @ {home}",
                        "time": et_time,
                        "state": state
                    })

        # =========================
        # OUTPUT (MLB STYLE)
        # =========================
        if games:

            for game in games:
                time_only = game["time"].split(" ")[1][:5] if game["time"] else "N/A"

                st.write(
                    f"{game['gamePk']} | 🏒 {game['matchup']} | 🕒 {time_only} (ET) | {game['state']}"
                )

        else:
            st.warning("No games found for this date")
