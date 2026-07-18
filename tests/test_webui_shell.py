"""Story 4.1 + SAMS.dc.html design: the five-page Web UI shell (FR-12,
UX-DR1/DR2/DR12).

Headless AppTest coverage of the router, the Quiet Clerk theme pin, the
verbatim empty-state microcopy, and the thin-adapter rule (AD-1/AD-8:
zero engine logic in pages). Router runs point SAMS_DB_PATH at a tmp dir so
the landing Dashboard never reads (or verifies signatures against) the real
working DB.
"""

import re
import tomllib
from pathlib import Path

import pytest

pytest.importorskip("streamlit.testing.v1")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WEBUI = ROOT / "webui"

# UX-DR2: exact sidebar titles, sentence-case, no other navigation.
PAGE_TITLES = (
    "Dashboard",
    "Mark today's attendance",
    "Session history",
    "Look up a student",
    "Check a signature",
)

# UX-DR12 / SAMS.dc.html: verbatim empty-state microcopy.
DASHBOARD_PROMPT = "A quick read on the class, then jump straight to what needs doing."
PROCESS_HINT = "Add the sheet photo and the info file, then tap Process. That's all you need to do."
HISTORY_PROMPT = "Every signing sheet you've processed, most recent first."
LOOKUP_PROMPT = "Type a student's number to see their attendance."
INVESTIGATE_PROMPT = "Type a student's number to check their signature."


def _page_test(page: str) -> AppTest:
    return AppTest.from_file(str(WEBUI / "pages" / page), default_timeout=30)


def _hermetic(tmp_path, monkeypatch) -> None:
    """Point the engine at an empty tmp DB for router-level runs (the landing
    Dashboard reads the DB; the suite must never touch the real one)."""
    from sams_core import config

    monkeypatch.setenv("SAMS_DB_PATH", str(tmp_path / "sams.db"))
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "sams.db")


# --- Theme (UX-DR1) -----------------------------------------------------------


def test_quiet_clerk_theme_pinned_light():
    config_path = ROOT / ".streamlit" / "config.toml"
    assert config_path.exists(), ".streamlit/config.toml missing — theme not applied"
    theme = tomllib.loads(config_path.read_text(encoding="utf-8"))["theme"]
    assert theme["primaryColor"] == "#44526A"
    assert theme["backgroundColor"] == "#FAFAF8"
    assert theme["secondaryBackgroundColor"] == "#FFFFFF"
    assert theme["textColor"] == "#33383F"
    assert theme["font"] == "sans serif"
    assert theme["base"] == "light", "light mode must be pinned (browser dark-mode never inverts)"


# --- Router (UX-DR2) ----------------------------------------------------------


def test_app_router_declares_exactly_the_five_pages():
    source = (WEBUI / "app.py").read_text(encoding="utf-8")
    for title in PAGE_TITLES:
        assert title in source, f"router missing page title {title!r}"
    assert source.count("st.Page(") == 5, "exactly five pages — no other navigation (UX-DR2)"
    assert "st.navigation" in source


def test_app_runs_and_lands_on_dashboard(tmp_path, monkeypatch):
    _hermetic(tmp_path, monkeypatch)
    at = AppTest.from_file(str(WEBUI / "app.py"), default_timeout=30).run()
    assert not at.exception
    body = " ".join(el.value for el in at.markdown) + " ".join(h.value for h in at.header)
    assert DASHBOARD_PROMPT in body


@pytest.mark.parametrize(
    ("page_path", "prompt"),
    [
        ("pages/Process.py", PROCESS_HINT),
        ("pages/History.py", HISTORY_PROMPT),
        ("pages/Lookup.py", LOOKUP_PROMPT),
        ("pages/Investigate.py", INVESTIGATE_PROMPT),
    ],
)
def test_router_navigates_to_each_non_default_page(page_path, prompt, tmp_path, monkeypatch):
    """Drive the non-default pages THROUGH the router — a typoed st.Page path
    or a page-level crash under st.navigation must fail here, not in a demo."""
    _hermetic(tmp_path, monkeypatch)
    at = AppTest.from_file(str(WEBUI / "app.py"), default_timeout=30).run()
    at.switch_page(page_path).run()
    assert not at.exception
    assert prompt in " ".join(el.value for el in at.markdown)


def test_ux_dr1_css_tokens_are_served(tmp_path, monkeypatch):
    """The chip/row CSS block is real delivery for Story 4.3 — pin its tokens
    so they cannot silently drift or vanish before they are consumed."""
    _hermetic(tmp_path, monkeypatch)
    at = AppTest.from_file(str(WEBUI / "app.py"), default_timeout=30).run()
    css = " ".join(el.value for el in at.markdown if "<style>" in el.value)
    for token in (
        "max-width: 1100px",
        "padding: 16px",
        "min-height: 52px",
        ".sams-chip-present { color: #256E4C; }",
        ".sams-chip-absent { color: #A63D2A; }",
        ".sams-chip-ambiguous { color: #7A6212; }",
        "background: none",
    ):
        assert token in css, f"UX-DR1/DR8 CSS token missing: {token!r}"


# --- Empty states (UX-DR12, verbatim) ------------------------------------------


def test_process_empty_state_two_slots_and_disabled_button():
    at = _page_test("Process.py").run()
    assert not at.exception
    body = " ".join(el.value for el in at.markdown)
    assert PROCESS_HINT in body
    labels = [u.label for u in at.get("file_uploader")]
    assert labels == ["Signing Sheet", "Info File"]
    # Exactly the two design actions on an empty page: a disabled Process and
    # the sample loader (SAMS design) — nothing else.
    buttons = {b.label: b for b in at.button}
    assert set(buttons) == {"Process", "Load sample sheet"}
    assert buttons["Process"].disabled is True, (
        "Process must be disabled with empty slots (UX-DR4)"
    )


def test_lookup_empty_state_prompt():
    at = _page_test("Lookup.py").run()
    assert not at.exception
    assert LOOKUP_PROMPT in " ".join(el.value for el in at.markdown)


def test_investigate_empty_state_prompt():
    at = _page_test("Investigate.py").run()
    assert not at.exception
    assert INVESTIGATE_PROMPT in " ".join(el.value for el in at.markdown)


# --- Thin adapters (AD-1/AD-8): zero engine logic in pages ---------------------


def test_pages_never_import_engine_internals():
    """Pages may import streamlit, matplotlib(backend), sams_core's public
    modules, and webui logic helpers — never cv2/numpy/sqlite3 directly:
    detection/persistence/visualization logic lives in the engine alone."""
    forbidden = re.compile(r"^\s*(?:import|from)\s+(?:[\w.]+\s*,\s*)*(cv2|numpy|sqlite3)\b", re.M)
    for page in sorted((WEBUI / "pages").glob("*.py")) + [WEBUI / "app.py"]:
        match = forbidden.search(page.read_text(encoding="utf-8"))
        assert not match, f"{page.name} imports {match.group(1)} — engine logic in a page (AD-8)"


def test_no_exclamation_marks_in_shell_copy():
    """Voice & Tone: no exclamation marks anywhere in operator-facing copy.
    AST-based: walks every string constant (multi-line and triple-quoted
    included), so copy cannot hide from a line regex. CSS/HTML blocks are
    exempt (not operator copy; '!important' is legitimate there)."""
    import ast

    for source in sorted(WEBUI.rglob("*.py")):
        if "__pycache__" in source.parts:
            continue
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                text = node.value
                if "<style>" in text or "</" in text:
                    continue
                assert "!" not in text, (
                    f"exclamation mark in copy at {source.name}:{node.lineno}: {text[:60]!r}"
                )
