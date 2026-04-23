import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# FUNCTIONS
# =========================

def parse_actual_time(raw_time):
    """Safely parse NHL UTC timestamps"""
    if not raw_time:
        return None
    try:
        return datetime.fromisoformat(
            raw_time.replace("Z", "+00:00")
        ).astimezone(ZoneInfo("America/New_York"))
    except:
        return None


def clock_to_seconds(clock):
    """Convert MM:SS → seconds"""
    if not clock:
        return None
    try:
        m, s = clock.split(":")
        return int(m) * 60 + int(s)
    except:
        return None


def normalize_period(period):
    """Convert OT periods into readable format"""
    if period is None:
        return None
    if period >= 4:
        return f"OT {period - 3}"
    return period


def group_period_for_filter(period):
    """Normalize OT grouping for filtering"""
    if isinstance(period, str) and period.startswith("OT"):
        return "OT"
    return period


def get_raw_timestamp(play):
    """
    NHL API does NOT guarantee timeUTC exists.
    Try multiple possible fields.
    """
    return (
        play.get("timeUTC")
        or play.get("eventTime")
        or play.get("about", {}).get("eventTime")
    )


# =========================
# UI
# =========================

st.title("🏒 NHL Dashboard")

game_id = st.text_input("Enter Game ID (gamePk)", "2024020123")

DEBUG = st.checkbox("Debug raw API", value=False)

# -------------------------
# Period Filter
# -------------------------
USE_PERIOD_FILTER = st.checkbox("Filter by Period", value=False)

TARGET_PERIODS = []

if USE_PERIOD_FILTER:
    TARGET_PERIODS = st.multiselect(
        "Select Periods",
        [1, 2, 3, "OT"],
        default=[2]
    )

# -------------------------
# Game Clock Filter
# -------------------------
USE_CLOCK_FILTER = st.checkbox("Filter by Game Clock", value=False)

MIN_CLOCK = None
MAX_CLOCK = None

if USE_CLOCK_FILTER:
    MIN_CLOCK = st.text_input("Min Clock (MM:SS)", "00:00")
    MAX_CLOCK = st.text_input("Max Clock (MM:SS)", "20:00")

# -------------------------
# Actual Time Filter
# -------------------------
USE_TIME_FILTER = st.checkbox("Filter by Actual Time (ET)", value=False)

et_now = datetime.now(ZoneInfo("America/New_York"))

today_start = et_now.replace(hour=0, minute=0, second=0, microsecond=0)
today_end = et_now.replace(hour=23, minute=59, second=0, microsecond=0)

START_TIME = None
END_TIME = None

if USE_TIME_FILTER:
    START_TIME = st.text_input(
        "Start Time (YYYY-MM-DD HH:MM)",
        value=today_start.strftime("%Y-%m-%d %H:%M"),
    )

    END_TIME = st.text_input(
        "End Time (YYYY-MM-DD HH:MM)",
        value=today_end.strftime("%Y-%m-%d %H:%M"),
    )

run = st.button("Load Game Feed")


# =========================
# MAIN LOGIC
# =========================

if run:
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            st.error(f"Bad response: {response.status_code}")
            st.stop()

        data = response.json()
        plays = data.get("plays", [])

        if DEBUG:
            st.write("RAW API SAMPLE")
            st.json(plays[:2])

        if not plays:
            st.warning("No plays found.")
            st.stop()

        # -------------------------
        # Filters setup
        # -------------------------

        START_SEC = None
        END_SEC = None

        if USE_CLOCK_FILTER and MIN_CLOCK and MAX_CLOCK:
            START_SEC = clock_to_seconds(MIN_CLOCK)
            END_SEC = clock_to_seconds(MAX_CLOCK)

        START_DT = None
        END_DT = None

        if USE_TIME_FILTER and START_TIME and END_TIME:
            START_DT = datetime.fromisoformat(START_TIME).replace(
                tzinfo=ZoneInfo("America/New_York")
            )
            END_DT = datetime.fromisoformat(END_TIME).replace(
                tzinfo=ZoneInfo("America/New_York")
            )

        # 🔥 IMPORTANT: sort by NHL's true timeline order
        plays = sorted(plays, key=lambda x: x.get("sortOrder", 0))

        events = []

        # =========================
        # PROCESS PLAYS
        # =========================
        for play in plays:

            raw_period = play.get("period")
            period_display = normalize_period(raw_period)
            period_group = group_period_for_filter(period_display)

            clock = play.get("timeInPeriod")
            raw_time = get_raw_timestamp(play)
            actual_dt = parse_actual_time(raw_time)

            # -------------------------
            # Period filter
            # -------------------------
            if USE_PERIOD_FILTER and period_group not in TARGET_PERIODS:
                continue

            # -------------------------
            # Clock filter
            # -------------------------
            if USE_CLOCK_FILTER:
                sec = clock_to_seconds(clock)
                if sec is not None and START_SEC is not None and END_SEC is not None:
                    if not (START_SEC <= sec <= END_SEC):
                        continue

            # -------------------------
            # Time filter
            # -------------------------
            if USE_TIME_FILTER and actual_dt and START_DT and END_DT:
                if not (START_DT <= actual_dt <= END_DT):
                    continue

            events.append({
                "Period": period_display,
                "Clock": clock,
                "Score": f"{play.get('awayScore')} - {play.get('homeScore')}",
                "Description": play.get("description"),
                "Event": play.get("typeDescKey"),
                "ET Time": (
                    actual_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
                    if actual_dt else "Not available"
                ),
                "SortOrder": play.get("sortOrder")
            })

        # =========================
        # OUTPUT
        # =========================

        st.success(f"Loaded {len(events)} events")

        for e in events:

            label = (
                f"🔥 {e['Period']}"
                if isinstance(e["Period"], str) and e["Period"].startswith("OT")
                else f"🏒 P{e['Period']}"
            )

            st.write(f"**{label} | ⏱️ {e['Clock']}**")
            st.write(f"📊 Score: {e['Score']}")
            st.write(f"📌 {e['Description']}")

            if e["Event"]:
                st.write(f"🎯 Event: {e['Event']}")

            st.write(f"🕒 ET Time: {e['ET Time']}")
            st.caption(f"SortOrder: {e['SortOrder']}")
            st.markdown("---")

    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
