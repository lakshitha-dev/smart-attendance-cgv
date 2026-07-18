"""Session history page (SAMS.dc.html design): thin adapter — the engine read
(`history_logic.history` over Story 2.1's repository), then headline tiles, a
small attendance trend, and one expander per saved session. ZERO grouping or
aggregate logic lives here (AD-1/AD-8) — `webui/history_logic.py` owns it; this
page is widgets + rendering only. Each student row links to their attendance
timeline on the Lookup page (prefilled via session state)."""

import html
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from sams_core.errors import SamsError
from sams_core.repository import AttendanceRepository
from webui.history_logic import history, rate_colour
from webui.process_logic import MUTED_INK, STATUS_CHIP

# st.set_page_config lives in app.py — the router owns the single call.
st.title("Session history")
st.markdown("Every signing sheet you've processed, most recent first.")

_HAIRLINE = "#E9E8E3"
_TILE = (
    "background:#FFFFFF;border:1px solid " + _HAIRLINE + ";border-radius:14px;"
    "box-shadow:0 1px 2px rgba(28,33,40,.05);padding:16px 18px"
)


def _stat_tile(value: str, label: str, colour: str) -> str:
    """One headline tile (SAMS.dc.html): big coloured figure over a muted label."""
    return (
        f"<div style='{_TILE}'>"
        f"<div style='font-size:2rem;font-weight:800;color:{colour};line-height:1;"
        f"font-variant-numeric:tabular-nums'>{html.escape(value)}</div>"
        f"<div style='color:{MUTED_INK};font-size:0.85rem;margin-top:3px'>{html.escape(label)}</div>"
        "</div>"
    )


def _trend_tile(sessions_oldest_first) -> str:
    """The ATTENDANCE TREND mini-bars: one indigo column per session, height
    proportional to its rate, dated underneath (decorative — the same numbers
    sit in each session row below, so colour/height is never the sole signal)."""
    columns = []
    for session in sessions_oldest_first:
        bar_height = max(6, round(session.rate / 100 * 44))
        columns.append(
            "<div style='flex:1;display:flex;flex-direction:column;align-items:center;"
            "gap:6px;justify-content:flex-end'>"
            f"<div style='width:30px;height:{bar_height}px;border-radius:7px 7px 3px 3px;"
            "background:linear-gradient(180deg,#6366F1,#4F46E5)'></div>"
            f"<div style='color:{MUTED_INK};font-size:0.68rem;font-variant-numeric:tabular-nums'>"
            f"{html.escape(session.sheet_id[5:])}</div></div>"
        )
    return (
        f"<div style='{_TILE};grid-column:1/-1'>"
        f"<div style='color:{MUTED_INK};font-weight:700;font-size:0.74rem;"
        "letter-spacing:0.06em;margin-bottom:6px'>ATTENDANCE TREND</div>"
        "<div style='display:flex;align-items:flex-end;gap:8px;height:64px'>"
        + "".join(columns)
        + "</div></div>"
    )


def _row_html(record) -> str:
    """One student row (UX-DR7/DR8): name + tabular index + status chip (icon +
    label + colour, no fill). Untrusted name/index are HTML-escaped."""
    icon, label, colour = STATUS_CHIP[record.status]
    name = html.escape(record.student_name or record.student_index)
    index = html.escape(record.student_index)
    return (
        "<div class='sams-row' style='display:flex;justify-content:space-between;"
        "align-items:baseline;gap:12px'>"
        f"<div><strong>{name}</strong><br>"
        f"<span style='color:{MUTED_INK};font-variant-numeric:tabular-nums;"
        f"font-size:0.85em'>{index}</span></div>"
        f"<div style='text-align:right;white-space:nowrap'>"
        f"<span style='color:{colour};font-weight:600'>{icon} {label}</span></div>"
        "</div>"
    )


def _summary_html(session) -> str:
    """One session's summary row (SAMS design): date + weekday left, the rate
    bar across the middle, the present split and the bold rate reading right."""
    if session.rate >= 80:
        fill = "linear-gradient(90deg,#34A97B,#256E4C)"
    elif session.rate >= 50:
        fill = "linear-gradient(90deg,#D8B94A,#7A6212)"
    else:
        fill = "linear-gradient(90deg,#C9603F,#A63D2A)"
    weekday = html.escape(session.weekday) if session.weekday else "&nbsp;"
    return (
        "<div style='display:flex;align-items:center;gap:16px'>"
        f"<div style='min-width:110px'>"
        f"<div style='font-weight:700;font-variant-numeric:tabular-nums'>{html.escape(session.sheet_id)}</div>"
        f"<div style='color:{MUTED_INK};font-size:0.82rem'>{weekday}</div></div>"
        "<div style='flex:1;min-width:80px;height:8px;border-radius:99px;background:#EEEDE8'>"
        f"<div style='height:100%;width:{session.rate}%;border-radius:99px;background:{fill}'></div></div>"
        f"<div style='min-width:100px;text-align:right;color:{MUTED_INK};font-size:0.85rem;"
        f"white-space:nowrap'>{session.present}/{session.total} present</div>"
        f"<div style='min-width:52px;text-align:right;font-weight:800;font-size:1.1rem;"
        f"color:{rate_colour(session.rate)}'>{session.rate}%</div>"
        "</div>"
    )


def _render(data) -> None:
    tiles = (
        "<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));"
        "gap:14px;margin-bottom:6px'>"
        + _stat_tile(str(data.total_sessions), "sessions recorded", "#4F46E5")
        + _stat_tile(f"{data.average_rate}%", "average attendance", "#256E4C")
        + _trend_tile(list(reversed(data.sessions)))
        + "</div>"
    )
    st.markdown(tiles, unsafe_allow_html=True)

    for session in data.sessions:
        with st.container(border=True):
            st.markdown(_summary_html(session), unsafe_allow_html=True)
            with st.expander(f"Students ({session.total})"):
                for record in session.records:
                    row_col, link_col = st.columns([5, 1], vertical_alignment="center")
                    row_col.markdown(_row_html(record), unsafe_allow_html=True)
                    if link_col.button(
                        "Timeline",
                        key=f"timeline_{session.sheet_id}_{record.student_index}",
                        type="tertiary",
                        help="View this student's attendance timeline",
                    ):
                        st.session_state["lookup_alias"] = record.student_index
                        st.switch_page("pages/Lookup.py")


data = None
try:
    data = history(AttendanceRepository())
except SamsError:
    st.error("Something went wrong reading the saved records.")
except Exception:  # AD-6: no raw traceback may reach the browser
    st.error("Something went wrong reading the saved records.")

if data is not None:
    if data.message:
        st.write(data.message)
    else:
        _render(data)
