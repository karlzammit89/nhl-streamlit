import streamlit as st
import requests
from datetime import datetime, timedelta
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

                dt_et = datetime.fromisoformat(start.replace("Z", "+00:00")) \
                    .astimezone(ZoneInfo("America/New_York"))

                if dt_et.date() != target_date_et:
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
# MODE 2 — GAME FEED (YOUR PLAY-BY-PLAY LOGIC)
# =========================================================
if mode == "Game Feed":

    game_id = st.text_input("Enter Game ID", "2025030181")

    if st.button("Load Game Feed"):

        url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

        def fetch_json(url):
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            return r.json()

        data = fetch_json(url)
        plays = data.get("plays", [])

        def normalize_clock(clock):
            try:
                mm, ss = map(int, clock.split(":"))
                total = mm * 60 + ss
                total = max(0, min(1200, total))
                mm = total // 60
                ss = total % 60
                return f"{mm:02d}:{ss:02d}"
            except:
                return "20:00"

        def sort_key(play):
            period = play.get("periodDescriptor", {}).get("number", 0)
            clock = normalize_clock(play.get("timeInPeriod", "20:00"))
            mm, ss = map(int, clock.split(":"))
            remaining = mm * 60 + ss
            return (period - 1) * 1200 + (1200 - remaining)

        plays = sorted(plays, key=sort_key)

        start_time_utc = data.get("startTimeUTC")
        game_start = datetime.fromisoformat(start_time_utc.replace("Z", "+00:00"))

        def build_event_time(period, clock):
            mm, ss = map(int, clock.split(":"))
            remaining = mm * 60 + ss
            elapsed = (1200 - remaining) + (period - 1) * 1200
            return (game_start + timedelta(seconds=elapsed)).astimezone(
                ZoneInfo("America/New_York")
            )

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
            raw_clock = play.get("timeInPeriod", "20:00")

            if not period:
                continue

            clock = normalize_clock(raw_clock)

            details = play.get("details", {})
            event = (play.get("typeDescKey") or "").lower()

            team_id = details.get("eventOwnerTeamId")
            team = home if team_id == home_id else away

            event_time = build_event_time(period, clock)
            time_str = event_time.strftime("%Y-%m-%d %H:%M:%S %Z")

            description = event.upper()

            if event == "goal":
                if team_id == home_id:
                    home_score += 1
                else:
                    away_score += 1

                player = details.get("scoringPlayer", {})
                name = f"{player.get('firstName','')} {player.get('lastName','')}"

                is_en = details.get("emptyNet") is True or str(details.get("strength","")).upper() == "EN"
                en_flag = " 🥅" if is_en else ""

                description = f"🚨 GOAL {team}{en_flag} | {name}"

            elif event == "penalty":
                description = f"⛔ PENALTY {team}"

            st.write("")
            st.write(time_str)
            st.write(f"P{period} | {clock}")
            st.write(f"{away} {away_score} - {home_score} {home}")
            st.write(description)
            st.divider()
