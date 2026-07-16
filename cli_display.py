"""CLI-side stage display helpers (AD-7: rendering lives in the adapter, never the engine).

`sams.py` stays a thin entry script (<50 lines, AD-1); the OpenCV window
mechanics live here. Stage windows are shown live DURING processing (FR-11),
each titled with its stage label, and held until a keypress when a real
operator is attached.

Display is gated on actual GUI availability, not on a stdin heuristic: the
first cv2 window failure (headless build, no display server) disables further
attempts for the run. Set SAMS_HEADLESS=1 to suppress windows explicitly
(the test suite does this via tests/conftest.py).
"""

import os
import sys

import cv2

from sams_core import config
from sams_core.models import StageArtifact

_gui_disabled = os.environ.get("SAMS_HEADLESS") == "1"


def show_stage_live(stage: StageArtifact) -> None:
    """Show one pipeline stage in a titled OpenCV window, without blocking."""
    global _gui_disabled
    if _gui_disabled or stage.image.size == 0:
        return
    display = stage.image if stage.image.ndim == 2 else cv2.cvtColor(stage.image, cv2.COLOR_RGB2BGR)
    scale = min(1.0, config.CLI_MAX_DISPLAY_DIM / max(display.shape[:2]))
    if scale < 1.0:
        display = cv2.resize(display, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    try:
        cv2.namedWindow(stage.label, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(stage.label, display.shape[1], display.shape[0])
        cv2.imshow(stage.label, display)
        cv2.waitKey(1)  # pump the window event loop so the stage appears live
    except cv2.error:
        _gui_disabled = True  # no GUI backend available: keep processing, skip display


def close_windows() -> None:
    """Tear down any open stage windows (also safe when none are open)."""
    if not _gui_disabled:
        cv2.destroyAllWindows()


def hold_windows_until_dismissed() -> None:
    """Keep the stage windows open until a keypress, then close them.

    The blocking wait only makes sense with an operator attached (a TTY);
    otherwise windows are closed immediately.
    """
    if _gui_disabled:
        return
    if sys.stdin.isatty():
        cv2.waitKey(0)
    cv2.destroyAllWindows()


def print_run_summary(result) -> None:
    """Per-student stdout summary after a successful run (UX-DR16).

    `result` is the engine's SheetResult: Attendance Records carry the
    canonical Student Index, name, and first-class status (Ambiguous included).
    The saved-count line reports what was actually written — rows preserved by
    an earlier operator resolution are called out via the engine's warning.
    """
    print(f"Parsed {len(result.records)} Student Records. Sheet Identifier: {result.sheet_id}")
    for warning in result.warnings:
        print(f"Warning: {warning}")
    for record in result.records:
        print(f"{record.student_index}  {record.student_name}: {record.status.value}")
    saved = result.persisted_count if result.persisted_count is not None else len(result.records)
    print(f"Saved {saved} Attendance Records to the Local DB.")
    print(f"Signature crops: {config.OUTPUT_DIR / str(result.sheet_id) / 'crops'}")
