import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# TITLE
# =========================
st.title("🏒 NHL Dashboard")

# =========================
# MODE (MLB STYLE)
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
# MODE 1 — SCHEDULE
# =========================
if mode == "Schedule":

    date = st.text_input("Enter date (YYYY-MM-DD)", "2026-04-20")

    if st.button("Load Games"):

        # ✅ target ET date
        target_date_et = datetime.fromisoformat(date).date()

        url = f"https://api-web.nhle.com/v1/schedule/{date}"

        try:
            data = requests.get(url, timeout=10).json()
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()

        games = []

        # =========================
        # PARSE ALL GAMES
        # =========================
        for week in data.get("gameWeek", []):
            for g in week.get("games", []):

                start_utc = g.get("startTimeUTC")
                if not start_utc:
                    continue

                # ✅ STEP 1: UTC → ET
                dt_et = datetime.fromisoformat(start_utc.replace("Z", "+00:00")) \
                    .astimezone(ZoneInfo("America/New_York"))

                # ✅ STEP 2: STRICT ET DATE FILTER (THIS FIXES YOUR ISSUE)
                if dt_et.date() != target_date_et:
                    continue

                games.append({
                    "gamePk": g.get("id"),
                    "matchup": f"{g['awayTeam']['abbrev']} @ {g['homeTeam']['abbrev']}",
                    "time": dt_et.strftime("%H:%M"),
                    "state": g.get("gameState")
                })

        # =========================
        # OUTPUT (MLB STYLE)
        # =========================
        if games:

            st.success(f"Found {len(games)} games on {date} (ET)")

            for game in games:
                st.write(
                    f"{game['gamePk']} | 🏒 {game['matchup']} | 🕒 {game['time']} (ET)}"
                )

        else:
            st.warning("No games found for this exact ET date")
