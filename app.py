import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# TITLE
# =========================
st.title("🏒 NHL Dashboard")

# =========================
# MODE
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


# =========================
# MODE — SCHEDULE
# =========================
if mode == "Schedule":

    date = st.text_input("Enter date (YYYY-MM-DD)", "2026-04-20")

    if st.button("Load Games"):

        target_date_et = datetime.fromisoformat(date).date()

        url = f"https://api-web.nhle.com/v1/schedule/{date}"

        try:
            data = requests.get(url, timeout=10).json()
        except:
            st.stop()

        games = []

        # =========================
        # PARSE GAMES
        # =========================
        for week in data.get("gameWeek", []):
            for g in week.get("games", []):

                start = g.get("startTimeUTC")
                if not start:
                    continue

                # UTC → ET
                dt_et = datetime.fromisoformat(start.replace("Z", "+00:00")) \
                    .astimezone(ZoneInfo("America/New_York"))

                # STRICT ET DATE FILTER
                if dt_et.date() != target_date_et:
                    continue

                games.append({
                    "gamePk": g.get("id"),
                    "matchup": f"{g['awayTeam']['abbrev']} @ {g['homeTeam']['abbrev']}",
                    "time": dt_et.strftime("%H:%M")
                })

        # =========================
        # OUTPUT (CLEAN)
        # =========================
        if games:

            for game in games:
                st.write(
                    f"{game['gamePk']} | 🏒 {game['matchup']} | 🕒 {game['time']} (ET)"
                )
