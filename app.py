import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st

st.set_page_config(page_title="NHL Games Viewer", page_icon="🏒")
st.title("🏒 NHL Games (Correct ET Filtering)")

col1, col2, col3 = st.columns(3)

with col1:
    year = st.number_input("Year", 2020, 2030, 2026)
with col2:
    month = st.number_input("Month", 1, 12, 4)
with col3:
    day = st.number_input("Day", 1, 31, 20)

if st.button("Get Games"):

    target_date_et = datetime(year, month, day).date()

    url = f"https://api-web.nhle.com/v1/schedule/{year}-{month:02d}-{day:02d}"

    try:
        data = requests.get(url, timeout=10).json()
    except Exception as e:
        st.error(f"API error: {e}")
        st.stop()

    games = []

    for week in data.get("gameWeek", []):
        for game in week.get("games", []):

            utc_time = game.get("startTimeUTC")
            if not utc_time:
                continue

            # ✅ PROPER UTC → ET CONVERSION (handles DST correctly)
            dt_utc = datetime.fromisoformat(utc_time.replace("Z", "+00:00"))
            dt_et = dt_utc.astimezone(ZoneInfo("America/New_York"))

            # filter by REAL ET date
            if dt_et.date() != target_date_et:
                continue

            games.append({
                "Game": f"{game['awayTeam']['abbrev']} @ {game['homeTeam']['abbrev']}",
                "Time (ET)": dt_et.strftime("%H:%M"),
                "Status": game.get("gameState")
            })

    st.subheader(f"Games on {target_date_et} (ET)")

    if games:
        st.dataframe(games, use_container_width=True)
    else:
        st.warning("No games found for this date.")
