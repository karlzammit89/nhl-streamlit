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
mode = st.radio("Select Mode", ["Schedule", "Game Feed"])

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


# =========================================================
# MODE 1 — SCHEDULE
# =========================================================
if mode == "Schedule":

    date = st.text_input("Enter date (YYYY-MM-DD)", "2026-04-20")

    if st.button("Load Games"):

        target_date_et = datetime.fromisoformat(date).date()

        url = f"https://api-web.nhle.com/v1/schedule/{date}"
        data = requests.get(url).json()

        games = []

        for week in data.get("gameWeek", []):
            for g in week.get("games", []):

                start = g.get("startTimeUTC")
                if not start:
                    continue

                dt_et = convert_to_et(start)

                if not dt_et or dt_et.date() != target_date_et:
                    continue

                games.append({
                    "gamePk": g.get("id"),
                    "matchup": f"{g['awayTeam']['abbrev']} @ {g['homeTeam']['abbrev']}",
                    "time": dt_et.strftime("%H:%M")
                })

        if games:
            for game in games:
                st.write(
                    f"{game['gamePk']} | 🏒 {game['matchup']} | 🕒 {game['time']} (ET)"
                )


# =========================================================
# MODE 2 — GAME FEED (RAW API ONLY)
# =========================================================
if mode == "Game Feed":

    game_id = st.text_input("Enter Game ID", "2025030181")

    if st.button("Load Game Feed"):

        url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

        try:
            data = requests.get(url, headers=headers, timeout=10).json()
        except:
            st.stop()

        plays = data.get("plays", [])

        # =========================
        # SORT CORRECTLY (NO FAKE TIME)
        # =========================
        def sort_key(play):
            period = play.get("periodDescriptor", {}).get("number", 0)

            clock = play.get("timeInPeriod", "20:00")
            try:
                mm, ss = map(int, clock.split(":"))
                remaining = mm * 60 + ss
            except:
                remaining = 1200

            # earlier plays = higher remaining time
            return (period, -remaining)

        plays = sorted(plays, key=sort_key)

        # =========================
        # TEAM INFO
        # =========================
        home = data.get("homeTeam", {}).get("abbrev", "HOME")
        away = data.get("awayTeam", {}).get("abbrev", "AWAY")

        home_id = data.get("homeTeam", {}).get("id")
        away_id = data.get("awayTeam", {}).get("id")

        home_score = 0
        away_score = 0

        # =========================
        # OUTPUT
        # =========================
        for play in plays:

            period = play.get("periodDescriptor", {}).get("number")
            clock = play.get("timeInPeriod")

            if not period or not clock:
                continue

            details = play.get("details", {})
            event = (play.get("typeDescKey") or "").lower()

            team_id = details.get("eventOwnerTeamId")
            team = home if team_id == home_id else away

            # ✅ USE RAW TIMESTAMP ONLY
            raw_time = play.get("timeInPeriodUTC") or play.get("timeUTC")
            dt_et = convert_to_et(raw_time)
            time_str = dt_et.strftime("%Y-%m-%d %H:%M:%S %Z") if dt_et else "N/A"

            description = event.upper()

            if event == "goal":
                if team_id == home_id:
                    home_score += 1
                else:
                    away_score += 1

                player = details.get("scoringPlayer", {})
                name = f"{player.get('firstName','')} {player.get('lastName','')}"

                is_en = details.get("emptyNet") is True or str(details.get("strength", "")).upper() == "EN"
                en_flag = " 🥅" if is_en else ""

                description = f"🚨 GOAL {team}{en_flag} | {name}"

            elif event == "penalty":
                description = f"⛔ PENALTY {team}"

            # =========================
            # DISPLAY
            # =========================
            st.write("")
            st.write(time_str)
            st.write(f"P{period} | {clock} remaining")
            st.write(f"{away} {away_score} - {home_score} {home}")
            st.write(description)
            st.divider()
