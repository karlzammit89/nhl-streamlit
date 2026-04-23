import requests
from datetime import datetime, timezone
import streamlit as st

st.set_page_config(page_title="NHL Games Viewer", page_icon="🏒")
st.title("🏒 NHL Games Viewer (ET Filter)")

col1, col2, col3 = st.columns(3)

with col1:
    year = st.number_input("Year", 2020, 2030, 2026)
with col2:
    month = st.number_input("Month", 1, 12, 4)
with col3:
    day = st.number_input("Day", 1, 31, 20)

if st.button("Get NHL Games"):

    target_date = datetime(year, month, day).date()

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

            dt = datetime.fromisoformat(utc_time.replace("Z", "+00:00"))
            dt_et = dt.astimezone(timezone.utc).replace(tzinfo=None)

            if dt_et.date() != target_date:
                continue

            games.append({
                "Game": f"{game['awayTeam']['abbrev']} @ {game['homeTeam']['abbrev']}",
                "Time": dt_et.strftime("%H:%M"),
                "Status": game.get("gameState")
            })

    st.subheader(f"Games on {target_date}")
    if games:
        st.dataframe(games)
    else:
        st.warning("No games found.")
