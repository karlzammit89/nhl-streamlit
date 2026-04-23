import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# FUNCTIONS
# =========================

def convert_to_et(raw_time):
    if raw_time:
        dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
        return dt.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S %Z")
    return None


def parse_actual_time(raw_time):
    if not raw_time:
        return None
    return datetime.fromisoformat(raw_time.replace("Z", "+00:00")).astimezone(
        ZoneInfo("America/New_York")
    )


def clock_to_seconds(clock):
    if not clock:
        return None
    try:
        m, s = clock.split(":")
        return int(m) * 60 + int(s)
    except:
        return None


def normalize_period(period):
    if period is None:
        return None
    if period >= 4:
        return f"OT {period - 3}"
    return period


def group_period_for_filter(period):
    if isinstance(period, str) and period.startswith("OT"):
        return "OT"
    return period


# =========================
# UI
# =========================

st.title("🏒 NHL Dashboard")

game_id = st.text_input("Enter Game ID (gamePk)", "2023020001")

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
    MIN_CLOCK = st.text_input("Min Clock (MM:SS)", "10:00")
    MAX_CLOCK = st.text_input("Max Clock (MM:SS)", "00:00")

# -------------------------
# Actual Time Filter
# -------------------------
USE_TIME_FILTER = st.checkbox("Filter by Actual Time (ET)", value=False)

et_now = datetime.now(ZoneInfo("America/New_York"))

today_start = et_now.replace(hour=0, minute=0, second=0, microsecond=0)
today_end = et_now.replace(hour=23, minute=59, second=0, microsecond=0)

if "start_time" not in st.session_state:
    st.session_state.start_time = today_start.strftime("%Y-%m-%d %H:%M")

if "end_time" not in st.session_state:
    st.session_state.end_time = today_end.strftime("%Y-%m-%d %H:%M")

START_TIME = None
END_TIME = None

if USE_TIME_FILTER:
    START_TIME = st.text_input(
        "Start Time (YYYY-MM-DD HH:MM)",
        value=st.session_state.start_time,
        key="start_time"
    )

    END_TIME = st.text_input(
        "End Time (YYYY-MM-DD HH:MM)",
        value=st.session_state.end_time,
        key="end_time"
    )

run = st.button("Load Game Feed")


# =========================
# MAIN LOGIC
# =========================

if run:
    url = f"https://statsapi.web.nhl.com/api/v1/game/{game_id}/feed/live"

    try:
        data = requests.get(url, timeout=10).json()
        plays = data.get("liveData", {}).get("plays", {}).get("allPlays", [])

        START_SEC = None
        END_SEC = None

        if USE_CLOCK_FILTER and MIN_CLOCK and MAX_CLOCK:
            START_SEC = clock_to_seconds(MAX_CLOCK)
            END_SEC = clock_to_seconds(MIN_CLOCK)

        START_DT = None
        END_DT = None

        if USE_TIME_FILTER and START_TIME and END_TIME:
            START_DT = datetime.fromisoformat(START_TIME).replace(
                tzinfo=ZoneInfo("America/New_York")
            )
            END_DT = datetime.fromisoformat(END_TIME).replace(
                tzinfo=ZoneInfo("America/New_York")
            )

        events = []

        for play in plays:
            about = play.get("about", {})
            result = play.get("result", {})

            raw_period = about.get("period")
            period_display = normalize_period(raw_period)
            period_group = group_period_for_filter(period_display)

            clock = about.get("periodTime")
            actual_dt = parse_actual_time(about.get("dateTime"))

            # Period filter
            if USE_PERIOD_FILTER and period_group not in TARGET_PERIODS:
                continue

            # Clock filter
            if USE_CLOCK_FILTER:
                sec = clock_to_seconds(clock)
                if sec is not None and START_SEC is not None and END_SEC is not None:
                    if not (START_SEC <= sec <= END_SEC):
                        continue

            # Time filter
            if USE_TIME_FILTER and actual_dt and START_DT and END_DT:
                if not (START_DT <= actual_dt <= END_DT):
                    continue

            events.append({
                "Period": period_display,
                "Clock": clock,
                "Score": f"{about.get('goals', {}).get('away')} - {about.get('goals', {}).get('home')}",
                "Description": result.get("description"),
                "Event": result.get("eventTypeId"),
                "ET Time": actual_dt.strftime("%Y-%m-%d %H:%M:%S %Z") if actual_dt else None
            })

        # =========================
        # OUTPUT
        # =========================

        for e in events:

            label = f"🔥 {e['Period']}" if str(e["Period"]).startswith("OT") else f"🏒 P{e['Period']}"

            st.write(f"**{label} | ⏱️ {e['Clock']}**")
            st.write(f"📊 Score: {e['Score']}")
            st.write(f"📌 {e['Description']}")

            if e["Event"]:
                st.write(f"🎯 Event: {e['Event']}")

            st.success(f"🕒 Timestamp: {e['ET Time']}")
            st.markdown("---")

        st.success(f"Loaded {len(events)} events")

    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
