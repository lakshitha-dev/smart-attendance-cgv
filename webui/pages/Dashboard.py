"""Dashboard — the landing page (SAMS.dc.html design): a quick read on the
class, then straight to what needs doing. Thin adapter (AD-1/AD-8) —
`webui/dashboard_logic.py` owns every number (range windows, per-student
rates, signature alerts via the Epic 3 engine); this page is widgets +
session-state memoisation + rendering only. Flagged students deep-link to
Lookup/Investigate with the student prefilled (session state), and the quick
actions are plain router switches."""

import html
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from sams_core import config
from sams_core.errors import SamsError
from sams_core.repository import AttendanceRepository
from webui.dashboard_logic import load_dashboard, range_view, signature_alerts
from webui.history_logic import rate_colour
from webui.process_logic import MUTED_INK

# st.set_page_config lives in app.py — the router owns the single call.
st.title("Dashboard")
st.markdown("A quick read on the class, then jump straight to what needs doing.")


def _overline(text: str) -> None:
    """The system's one overline (DESIGN.md): muted-ink, uppercase, tracked."""
    st.markdown(
        f"<div style='color:{MUTED_INK};font-weight:700;font-size:0.8rem;"
        f"letter-spacing:0.06em'>{html.escape(text)}</div>",
        unsafe_allow_html=True,
    )


def _memo(key: str, token, compute):
    """Cache a computed value against a token (the DB file's mtime here) in
    session state so reruns don't re-verify every signature; recompute only
    when the DB actually changed."""
    store = st.session_state.setdefault("_memo", {})
    if store.get(key, (None,))[0] != token:
        store[key] = (token, compute())
    return store[key][1]


def _db_token():
    try:
        return config.DB_PATH.stat().st_mtime_ns
    except OSError:
        return None


def _stat_tile(value: str, label: str, colour: str) -> str:
    """One headline tile (SAMS.dc.html): big coloured figure over a muted label.
    Shape comes from the shared .sams-tile class in app.py — only the figure's
    colour varies per tile, so only that stays inline (a class rule cannot
    override an inline declaration, which the phone breakpoint needs to do)."""
    return (
        "<div class='sams-tile'>"
        f"<div style='font-size:2rem;font-weight:800;color:{colour};line-height:1;"
        f"font-variant-numeric:tabular-nums'>{html.escape(value)}</div>"
        f"<div style='color:{MUTED_INK};font-size:0.85rem;margin-top:3px'>{html.escape(label)}</div>"
        "</div>"
    )


def _rate_bar(rate: int) -> str:
    """The session rate as a soft progress bar, hue matched to the reading."""
    if rate >= 80:
        fill = "linear-gradient(90deg,#34A97B,#256E4C)"
    elif rate >= 50:
        fill = "linear-gradient(90deg,#D8B94A,#7A6212)"
    else:
        fill = "linear-gradient(90deg,#C9603F,#A63D2A)"
    return (
        "<div style='height:8px;border-radius:99px;background:#EEEDE8;margin:12px 0 10px'>"
        f"<div style='height:100%;width:{rate}%;border-radius:99px;background:{fill}'></div></div>"
    )


def _latest_session_card(latest) -> None:
    """LATEST SESSION (SAMS.dc.html): date + weekday, the rate reading with its
    bar, the present/absent split, and the jump to Session history."""
    _overline("LATEST SESSION")
    weekday = html.escape(latest.weekday) if latest.weekday else "&nbsp;"
    st.markdown(
        "<div style='display:flex;justify-content:space-between;align-items:flex-start;"
        "gap:12px;margin-top:8px'>"
        f"<div><div style='font-weight:700;font-size:1.15rem;font-variant-numeric:tabular-nums'>"
        f"{html.escape(latest.sheet_id)}</div>"
        f"<div style='color:{MUTED_INK};font-size:0.85rem'>{weekday}</div></div>"
        f"<div style='text-align:right'><div style='font-size:1.8rem;font-weight:800;"
        f"line-height:1;color:{rate_colour(latest.rate)}'>{latest.rate}%</div>"
        f"<div style='color:{MUTED_INK};font-size:0.8rem'>attendance</div></div></div>"
        + _rate_bar(latest.rate)
        + f"<div style='display:flex;gap:18px;color:{MUTED_INK};font-size:0.85rem'>"
        f"<span><span style='color:#256E4C;font-weight:700'>●</span> {latest.present} present</span>"
        f"<span><span style='color:#A63D2A;font-weight:700'>●</span> {latest.absent} absent</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    # A button + switch_page rather than st.page_link: page_link resolves the
    # router's page registry, which is absent when this page runs standalone
    # (headless AppTest) — the button renders identically and stays testable.
    if st.button("All sessions →", key="latest_all_sessions", type="tertiary"):
        st.switch_page("pages/History.py")


def _needs_attention_card(low_attendance, alerts) -> None:
    """NEEDS ATTENTION (SAMS.dc.html): low-attendance students and signature
    alerts, each row a real button (keyboard-operable, UX-DR14) deep-linking
    to the matching page with the student prefilled."""
    _overline("NEEDS ATTENTION")
    if not low_attendance and not alerts:
        st.markdown(
            "<div style='color:#256E4C;font-weight:600;margin-top:8px'>"
            "✓ Nothing flagged — everyone's on track.</div>",
            unsafe_allow_html=True,
        )
        return
    if low_attendance:
        st.markdown(
            f"<div style='color:#A63D2A;font-weight:700;font-size:0.78rem;margin-top:6px'>"
            f"Low attendance ({len(low_attendance)})</div>",
            unsafe_allow_html=True,
        )
        for student in low_attendance:
            if st.button(
                f"{student.name} · {student.rate}% →",
                key=f"low_{student.student_index}",
                type="tertiary",
                help="View attendance timeline",
            ):
                st.session_state["lookup_alias"] = student.no or student.student_index
                st.switch_page("pages/Lookup.py")
    if alerts:
        st.markdown(
            f"<div style='color:#7A6212;font-weight:700;font-size:0.78rem;margin-top:6px'>"
            f"Signature alerts ({len(alerts)})</div>",
            unsafe_allow_html=True,
        )
        for alert in alerts:
            if st.button(
                f"{alert.name} · score {alert.score} →",
                key=f"sig_{alert.student_index}",
                type="tertiary",
                help="Check this signature",
            ):
                st.session_state["investigate_alias"] = alert.no or alert.student_index
                st.switch_page("pages/Investigate.py")


def _render_overview(data, repository) -> None:
    # DATE RANGE card (SAMS design): from → to dropdowns over the saved
    # sessions, summary right. Labels are collapsed because the overline IS
    # the visible group label; range_view swaps an inverted pair.
    dates = [s.sheet_id for s in data.sessions]
    with st.container(border=True, key="date_range"):
        label_col, from_col, arrow_col, to_col, sum_col = st.columns(
            [1.3, 1.6, 0.25, 1.6, 2.8], vertical_alignment="center"
        )
        with label_col:
            _overline("DATE RANGE")
        range_from = from_col.selectbox(
            "From", dates, index=0, key="dash_from", label_visibility="collapsed"
        )
        arrow_col.markdown(f"<span style='color:{MUTED_INK}'>→</span>", unsafe_allow_html=True)
        range_to = to_col.selectbox(
            "To", dates, index=len(dates) - 1, key="dash_to", label_visibility="collapsed"
        )
        view = range_view(data, dates.index(range_from), dates.index(range_to))
        sum_col.markdown(
            f"<div class='sams-range-summary'>{html.escape(view.summary)}</div>",
            unsafe_allow_html=True,
        )

    with st.spinner("Checking signatures…"):
        alerts = _memo(
            "dash_alerts", _db_token(), lambda: signature_alerts(data, repository)
        )
    flagged = len(view.low_attendance) + len(alerts)

    st.markdown(
        "<div class='sams-stat-grid'>"
        + _stat_tile(str(view.roster_count), "students on roster", "#4F46E5")
        + _stat_tile(str(view.session_count), "sessions recorded", "#33383F")
        + _stat_tile(f"{view.average_rate}%", "average attendance", "#256E4C")
        + _stat_tile(str(flagged), "need attention", "#7A6212")
        + "</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left, st.container(border=True):
        _latest_session_card(view.latest)
    with right, st.container(border=True):
        _needs_attention_card(view.low_attendance, alerts)


def _quick_actions() -> None:
    """QUICK ACTIONS: four tall left-aligned icon cards, as real router
    switches (the card body is the button's markdown label; the
    .st-key-quick_actions CSS in app.py gives the card shape). Rendered FIRST
    on the page — marking today's attendance is the system's main function,
    so its primary card leads before any read-only overview."""
    _overline("QUICK ACTIONS")
    actions = (
        ("▤", "Mark attendance", "Process a new signing sheet", "pages/Process.py", "primary"),
        ("▦", "Session history", "Review past sessions", "pages/History.py", "secondary"),
        ("◷", "Look up a student", "See an attendance timeline", "pages/Lookup.py", "secondary"),
        ("✎", "Check a signature", "Verify against references", "pages/Investigate.py", "secondary"),
    )
    with st.container(key="quick_actions"):
        columns = st.columns(len(actions))
        for column, (icon, title, caption, page, kind) in zip(columns, actions):
            icon_line = icon if kind == "primary" else f":violet[{icon}]"
            caption_line = caption if kind == "primary" else f":gray[{caption}]"
            label = f"{icon_line}  \n**{title}**  \n{caption_line}"
            if column.button(label, key=f"quick_{page}", type=kind, width="stretch"):
                st.switch_page(page)


repository = AttendanceRepository()
data = None
try:
    data = load_dashboard(repository)
except SamsError:
    st.error("Something went wrong reading the saved records.")
except Exception:  # AD-6: no raw traceback may reach the browser
    st.error("Something went wrong reading the saved records.")

if data is not None:
    _quick_actions()
    if data.message:
        st.write(data.message)
    else:
        try:
            _render_overview(data, repository)
        except SamsError:
            st.error("Something went wrong reading the saved records.")
        except Exception:
            st.error("Something went wrong reading the saved records.")
