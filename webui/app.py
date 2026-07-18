"""SAMS web entry point (Story 4.1 + SAMS.dc.html design, FR-12/UX-DR1/UX-DR2):
the five-page shell. `st.navigation` declares EXACTLY Dashboard (landing),
Process, History, Lookup, and Investigate — no other navigation, and `pages/`
auto-discovery is disabled by the explicit router. Theme lives in
.streamlit/config.toml (Quiet Clerk, light-pinned); this file adds only the
minimal chip/row CSS (UX-DR1) and owns the single st.set_page_config call."""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

# No page_title here: st.navigation titles each browser tab per page
# ("Mark today's attendance", …) — a pinned title would flatten them all to
# one string. layout="wide" + the CSS cap below give the ~1100px content
# width honestly (centered layout would fight the cap with its own ~46rem).
st.set_page_config(layout="wide")

# Quiet Clerk CSS layer (DESIGN.md tokens, elevated finish). The palette and
# the six theme values live in .streamlit/config.toml; this block adds the
# premium finish config can't express — soft shadows, refined type + rhythm,
# a sidebar wordmark, and smooth micro-interactions — while keeping the exact
# token substrings the tests pin (max-width: 1100px, padding: 16px,
# min-height: 52px, the three .sams-chip-* rules, background: none) and the
# UX-DR14 44px touch floor / hidden dev chrome. Chip colours per UX-DR8:
# coloured text/glyph only, never a filled background.
st.markdown(
    """
    <style>
    :root {
        --sams-paper: #FAFAF8;
        --sams-surface: #FFFFFF;
        --sams-primary: #44526A;
        --sams-primary-strong: #3B4860;
        --sams-primary-deep: #323D52;
        --sams-primary-tint: rgba(68, 82, 106, 0.07);
        --sams-primary-ring: rgba(68, 82, 106, 0.30);
        /* Vibrant indigo accent — the action colour that carries the UI's colour
           (button, links, focus, active nav, hovers). Status green/red/ochre
           stay reserved for attendance statuses. */
        --sams-accent: #4F46E5;
        --sams-accent-hi: #6366F1;
        --sams-accent-strong: #4338CA;
        --sams-accent-deep: #3730A3;
        --sams-accent-soft: #EEF1FF;
        --sams-accent-tint: rgba(79, 70, 229, 0.08);
        --sams-accent-ring: rgba(79, 70, 229, 0.32);
        --sams-accent-shadow: 0 2px 6px rgba(79, 70, 229, 0.26), 0 10px 22px rgba(79, 70, 229, 0.20);
        --sams-ink: #33383F;
        --sams-ink-muted: #7B818A;
        --sams-hairline: #E9E8E3;
        --sams-hairline-strong: #DAD8D1;
        --sams-row-hover: #F3F2EE;
        --sams-shadow-xs: 0 1px 2px rgba(28, 33, 40, 0.05);
        --sams-shadow-sm: 0 1px 2px rgba(28, 33, 40, 0.04), 0 2px 8px rgba(28, 33, 40, 0.05);
        --sams-shadow-md: 0 2px 6px rgba(28, 33, 40, 0.05), 0 12px 28px rgba(28, 33, 40, 0.07);
        --sams-shadow-primary: 0 2px 5px rgba(50, 61, 82, 0.22), 0 6px 16px rgba(50, 61, 82, 0.16);
        --sams-radius-sm: 10px;
        --sams-radius-md: 12px;
        --sams-radius-lg: 14px;
        --sams-ease: cubic-bezier(0.22, 1, 0.36, 1);
        --sams-dur: 190ms;
    }

    /* ---- Canvas + page chrome ---- */
    .stApp { background-color: var(--sams-paper);
        background-image: linear-gradient(180deg, #E9ECFF 0%, #F2F1FC 16%, rgba(250, 250, 248, 0) 46%),
                          radial-gradient(1200px 460px at 88% -6%, rgba(99, 102, 241, 0.10), rgba(99, 102, 241, 0) 70%);
        background-attachment: fixed; -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility; }
    /* Sticky translucent header bar (SAMS design): hairline + blur; the
       session chip content is injected by a second style block below (it
       carries a value read from the DB, so it cannot live in this literal). */
    [data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0.72);
        backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
        border-bottom: 1px solid #EFEEE9; box-shadow: none;
    }
    .stAppDeployButton { display: none; }  /* dev-only chrome, not part of SAMS */

    /* ---- Content column ---- */
    .block-container { max-width: 1100px; margin: 0 auto; padding-left: 18px; padding-right: 18px; padding-top: 2.75rem; padding-bottom: 4rem; }

    /* ---- Typography ---- */
    /* Colour on .stApp only (inherited) — never force it on every <p>, or the
       colour would leak into widget labels rendered as markdown paragraphs
       (e.g. the primary button's white label). */
    .stApp { color: var(--sams-ink); }
    .stApp p, .stApp li { line-height: 1.62; }
    .stApp h1 { font-weight: 700; letter-spacing: -0.021em; color: var(--sams-ink); font-size: 2rem; line-height: 1.18; margin-bottom: 0.1rem; }
    .stApp h2 { font-weight: 650; letter-spacing: -0.013em; font-size: 1.32rem; margin-top: 0.35rem; }
    .stApp h3 { font-weight: 650; letter-spacing: -0.008em; font-size: 1.08rem; }
    [data-testid="stCaptionContainer"], .stApp small { color: var(--sams-ink-muted); }
    .stApp a { color: var(--sams-accent); text-decoration: none; font-weight: 600; }
    .stApp a:hover { color: var(--sams-accent-strong); text-decoration: underline; }

    /* ---- Sidebar + native navigation ---- */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #FBFBFF 0%, var(--sams-surface) 100%); border-right: 1px solid var(--sams-hairline); }
    [data-testid="stSidebarNav"]::before {
        content: "SAMS";
        display: block;
        padding: 1.15rem 1.1rem 0;
        font-size: 1.05rem; font-weight: 800; letter-spacing: 0.16em;
        background: linear-gradient(90deg, var(--sams-accent) 0%, var(--sams-accent-hi) 100%);
        -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
    }
    /* Wordmark subtitle + hairline under the brand block (SAMS design header). */
    [data-testid="stSidebarNavItems"]::before {
        content: "Smart Attendance Management";
        display: block;
        padding: 3px 1.1rem 0.9rem;
        margin: 0 0 0.4rem;
        font-size: 0.72rem; color: var(--sams-ink-muted); letter-spacing: 0.02em;
        border-bottom: 1px solid var(--sams-hairline);
    }
    /* Course footer pinned to the sidebar's bottom edge (SAMS design). */
    [data-testid="stSidebar"]::after {
        content: "CS402.3 · Computer Graphics\\ANSBM Green University Town";
        white-space: pre-line;
        position: absolute; left: 0; right: 0; bottom: 0;
        padding: 12px 1.1rem 14px;
        font-size: 0.72rem; line-height: 1.5; color: var(--sams-ink-muted);
        border-top: 1px solid var(--sams-hairline);
        background: var(--sams-surface);
    }
    [data-testid="stSidebarNav"] a {
        border-radius: 10px; margin: 2px 8px; padding: 0.5rem 0.75rem;
        color: var(--sams-ink); font-weight: 500; border-left: 3px solid transparent;
        transition: background var(--sams-dur) var(--sams-ease), color var(--sams-dur) var(--sams-ease), border-color var(--sams-dur) var(--sams-ease);
    }
    [data-testid="stSidebarNav"] a:hover { background: var(--sams-accent-soft); color: var(--sams-accent-strong); }
    [data-testid="stSidebarNav"] a[aria-current="page"] { background: var(--sams-accent-soft); color: var(--sams-accent-strong); font-weight: 650; border-left-color: var(--sams-accent); }

    /* ---- Buttons ---- */
    .stButton button { min-height: 52px; border-radius: 12px; font-weight: 600; letter-spacing: 0.005em;
        transition: transform var(--sams-dur) var(--sams-ease), box-shadow var(--sams-dur) var(--sams-ease), background var(--sams-dur) var(--sams-ease), border-color var(--sams-dur) var(--sams-ease); }
    [data-testid="stBaseButton-primary"] {
        background: linear-gradient(180deg, var(--sams-accent-hi) 0%, var(--sams-accent) 100%);
        border: 1px solid var(--sams-accent-strong); color: #FFFFFF; box-shadow: var(--sams-accent-shadow);
    }
    [data-testid="stBaseButton-primary"]:hover:not(:disabled) {
        background: linear-gradient(180deg, var(--sams-accent) 0%, var(--sams-accent-strong) 100%);
        transform: translateY(-1px); box-shadow: 0 5px 12px rgba(79, 70, 229, 0.32), 0 14px 28px rgba(79, 70, 229, 0.24);
    }
    [data-testid="stBaseButton-primary"]:active:not(:disabled) { transform: translateY(0); box-shadow: 0 1px 3px rgba(55, 48, 163, 0.34) inset; }
    [data-testid="stBaseButton-primary"]:disabled { background: #EEEDE8; border-color: var(--sams-hairline); color: #AEB2B8; box-shadow: none; }
    /* Labels render inside a markdown <p>; inherit the button colour so the
       primary label stays white (enabled) / muted (disabled), the secondary
       label stays ink — never body-text ink on a slate button. */
    [data-testid="stBaseButton-primary"] p, [data-testid="stBaseButton-secondary"] p { color: inherit; }
    [data-testid="stBaseButton-secondary"] { background: var(--sams-surface); border: 1px solid var(--sams-hairline); color: var(--sams-ink); box-shadow: var(--sams-shadow-xs); }
    [data-testid="stBaseButton-secondary"]:hover:not(:disabled) { border-color: var(--sams-accent); color: var(--sams-accent-strong); background: var(--sams-accent-soft); transform: translateY(-1px); box-shadow: var(--sams-shadow-sm); }
    [data-testid="stBaseButton-secondary"]:active:not(:disabled) { transform: translateY(0); box-shadow: var(--sams-shadow-xs); }

    /* ---- Focus ring (keyboard) ---- */
    button:focus-visible, .stApp a:focus-visible, input:focus-visible {
        outline: none; box-shadow: 0 0 0 3px var(--sams-accent-ring); border-color: var(--sams-accent);
    }
    .stTextInput [data-baseweb="input"]:focus-within { box-shadow: 0 0 0 3px var(--sams-accent-ring); border-color: var(--sams-accent); }

    /* ---- Text input ---- */
    .stTextInput [data-baseweb="input"] { border-radius: var(--sams-radius-md); background: var(--sams-surface);
        transition: box-shadow var(--sams-dur) var(--sams-ease), border-color var(--sams-dur) var(--sams-ease); }
    .stTextInput input { padding-top: 0.6rem; padding-bottom: 0.6rem; }

    /* ---- File uploader ---- */
    [data-testid="stFileUploaderDropzone"] {
        background: var(--sams-surface); border: 1px dashed var(--sams-hairline-strong); border-radius: var(--sams-radius-lg);
        box-shadow: var(--sams-shadow-xs); padding: 1rem 1.25rem;
        transition: border-color var(--sams-dur) var(--sams-ease), background var(--sams-dur) var(--sams-ease), box-shadow var(--sams-dur) var(--sams-ease);
    }
    [data-testid="stFileUploaderDropzone"]:hover { border-color: var(--sams-accent); background: var(--sams-accent-soft); box-shadow: var(--sams-shadow-sm); }
    /* UX-DR14 44px touch floor: uploader Browse buttons + Streamlit nav chrome. */
    [data-testid='stFileUploader'] button, [data-testid='stDownloadButton'] button { min-height: 44px; }
    [data-testid='stExpandSidebarButton'] button, [data-testid='stExpandSidebarButton'],
    [data-testid='stMainMenuButton'], [data-testid='stBaseButton-headerNoPadding'] {
        min-height: 44px; min-width: 44px;
    }

    /* ---- Expander + status strip (pipeline stages) ---- */
    [data-testid="stExpander"] { border: 1px solid var(--sams-hairline); border-radius: var(--sams-radius-md);
        background: var(--sams-surface); box-shadow: var(--sams-shadow-xs); overflow: hidden;
        transition: box-shadow var(--sams-dur) var(--sams-ease), border-color var(--sams-dur) var(--sams-ease); }
    [data-testid="stExpander"]:hover { box-shadow: var(--sams-shadow-sm); border-color: var(--sams-hairline-strong); }
    [data-testid="stExpander"] summary { font-weight: 600; }
    [data-testid="stExpander"] summary:hover { color: var(--sams-accent); }
    [data-testid="stStatus"] { border-radius: var(--sams-radius-lg); border: 1px solid var(--sams-hairline); box-shadow: var(--sams-shadow-sm); }

    /* ---- Alerts (kept calm: soft tint, hairline, no shout) ---- */
    [data-testid="stAlert"] { border-radius: var(--sams-radius-md); border: 1px solid var(--sams-hairline); box-shadow: var(--sams-shadow-xs); }

    /* ---- Evidence images (square inside a soft frame) ---- */
    [data-testid="stImage"] img { border-radius: var(--sams-radius-sm); border: 1px solid var(--sams-hairline); }

    /* ---- Result list (Story 4.3): card, rows, status chips ---- */
    .sams-card { padding: 16px; border-radius: 14px; background: #FFFFFF; border: 1px solid var(--sams-hairline); box-shadow: var(--sams-shadow-sm); }
    .sams-row { padding: 10px 16px; border-radius: 10px; border: 1px solid transparent;
        transition: background var(--sams-dur) var(--sams-ease), border-color var(--sams-dur) var(--sams-ease); }
    .sams-row:hover { background: #F3F2EE; border-color: var(--sams-hairline); }
    .sams-chip { font-weight: 600; background: none; }
    .sams-chip-present { color: #256E4C; }
    .sams-chip-absent { color: #A63D2A; }
    .sams-chip-ambiguous { color: #7A6212; }

    /* ---- File dropzones (SAMS design microcopy + centered column) ---- */
    [data-testid="stFileUploaderDropzone"] { flex-direction: column; gap: 10px; text-align: center; }
    [data-testid="stFileUploaderDropzone"] svg { display: none; }  /* no cloud icon in the design */
    [data-testid="stFileUploaderDropzoneInstructions"] { margin-right: 0; }
    [data-testid="stFileUploaderDropzoneInstructions"] > div { display: none; }
    [data-testid="stFileUploaderDropzoneInstructions"]::before {
        color: var(--sams-ink-muted); font-size: 0.88rem;
    }
    .st-key-sheet_slot [data-testid="stFileUploaderDropzoneInstructions"]::before {
        content: "Tap to take a photo or drop a JPEG / PNG";
    }
    .st-key-info_slot [data-testid="stFileUploaderDropzoneInstructions"]::before {
        content: "Drop the class info.xml here";
    }

    /* ---- Quick-action cards (Dashboard, SAMS design) ---- */
    .st-key-quick_actions .stButton button {
        min-height: 118px; align-items: flex-start; text-align: left; padding: 14px 18px;
    }
    .st-key-quick_actions .stButton button > div { text-align: left; width: 100%; }
    .st-key-quick_actions .stButton button p { line-height: 1.45; }

    /* ---- Quick-pick student pills (Lookup/Investigate, SAMS design) ---- */
    .st-key-quick_pick .stButton button {
        border-radius: 99px; min-height: 44px; font-weight: 600;
        font-variant-numeric: tabular-nums;
    }

    /* ---- Expanders nested inside a bordered card (Session history) ---- */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stExpander"] {
        border: none; box-shadow: none;
    }
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stExpander"]:hover {
        border: none; box-shadow: none;
    }

    /* ---- Scrollbar ---- */
    *::-webkit-scrollbar { width: 10px; height: 10px; }
    *::-webkit-scrollbar-thumb { background: #DCDAD3; border-radius: 8px; border: 2px solid var(--sams-paper); }
    *::-webkit-scrollbar-thumb:hover { background: #C9C7BF; }
    *::-webkit-scrollbar-track { background: transparent; }

    /* ---- Respect reduced-motion ---- */
    @media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)

def _session_chip_css() -> str | None:
    """The header's "● Session · 10 Jul 2019" chip (SAMS design): the latest
    saved Sheet Identifier, injected as CSS content (the header bar is
    Streamlit chrome — no widget can render into it). Read-only and fully
    guarded: no DB, no sessions, or a non-date identifier simply means no chip.
    """
    from datetime import date

    from sams_core.repository import AttendanceRepository

    try:
        repository = AttendanceRepository()
        if not repository.db_exists:
            return None
        sheets = {record.sheet_id for record in repository.get_attendance()}
        if not sheets:
            return None
        latest = date.fromisoformat(max(sheets)).strftime("%d %b %Y")
    except Exception:
        return None
    return (
        "<style>"
        '[data-testid="stHeader"]::after {'
        f' content: "🟢 Session · {latest}";'
        " position: absolute; right: 24px; top: 50%; transform: translateY(-50%);"
        " color: #7B818A; font-size: 0.85rem; white-space: nowrap; }"
        "</style>"
    )


_chip = _session_chip_css()
if _chip:
    st.markdown(_chip, unsafe_allow_html=True)

pages = [
    st.Page("pages/Dashboard.py", title="Dashboard", default=True, icon=":material/home:"),
    st.Page("pages/Process.py", title="Mark today's attendance", icon=":material/list_alt:"),
    st.Page("pages/History.py", title="Session history", icon=":material/grid_on:"),
    st.Page("pages/Lookup.py", title="Look up a student", icon=":material/schedule:"),
    st.Page("pages/Investigate.py", title="Check a signature", icon=":material/edit:"),
]
st.navigation(pages).run()
