"""Attendance timeline chart (FR-8, AD-7): renders per-Session Present/Absent
history from Attendance Records already in hand — no DB access, no image
re-processing.

`render_attendance_timeline` returns a Matplotlib `Figure` and never calls
`plt.show()`: the CLI adapter (`infovis.py`, via `cli_display.show_figure`)
displays it, and the Web UI later renders the identical `Figure` object via
`st.pyplot` (FR-14 data-layer parity) — styling lives here exactly once.
"""

from collections.abc import Sequence

from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from sams_core.models import AttendanceRecord, AttendanceStatus

# Status -> (y-position, colour, icon, legend label). Ambiguous sits on its
# own mid-band (y=0) strictly between Absent (-1) and Present (1). Colours
# and icons per UX-DR8: icon + text + colour together, colour never the sole
# carrier (greyscale-survivable).
_STATUS_STYLE = {
    AttendanceStatus.ABSENT: {"y": -1, "color": "#A63D2A", "icon": "✕", "label": "Absent"},
    AttendanceStatus.AMBIGUOUS: {"y": 0, "color": "#7A6212", "icon": "?", "label": "Ambiguous"},
    AttendanceStatus.PRESENT: {"y": 1, "color": "#256E4C", "icon": "✓", "label": "Present"},
}
# Legend reads Present / Absent / Ambiguous (AC order), independent of y-position order.
_LEGEND_ORDER = (AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.AMBIGUOUS)


def _attendance_rate_caption(records: Sequence[AttendanceRecord]) -> str:
    """Present / (Present + Absent); Ambiguous is pending and excluded from
    both sides of the ratio (Dev Notes), reported separately instead."""
    present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
    ambiguous = sum(1 for r in records if r.status == AttendanceStatus.AMBIGUOUS)
    counted = present + absent
    rate = (present / counted * 100) if counted else 0.0
    caption = f"Attendance rate: {rate:.0f}% ({present}/{counted} sessions marked"
    if ambiguous:
        caption += f", {ambiguous} pending)"
    else:
        caption += ")"
    return caption


def render_attendance_timeline(records: Sequence[AttendanceRecord]) -> Figure:
    """Render one student's per-Session attendance timeline (FR-8).

    `records` is one student's Attendance Records (Story 2.1's
    `query_attendance` result); order is not assumed — sorted here by Sheet
    Identifier so the timeline reads chronologically left to right.
    """
    import matplotlib.pyplot as plt

    ordered = sorted(records, key=lambda r: r.sheet_id)
    x_positions = range(len(ordered))
    y_positions = [_STATUS_STYLE[r.status]["y"] for r in ordered]
    colors = [_STATUS_STYLE[r.status]["color"] for r in ordered]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(x_positions, y_positions, color="#B9B4A6", linewidth=1, zorder=1)
    ax.scatter(x_positions, y_positions, c=colors, s=140, zorder=3)
    for xi, record in zip(x_positions, ordered):
        style = _STATUS_STYLE[record.status]
        ax.annotate(
            style["icon"],
            (xi, style["y"]),
            ha="center",
            va="center",
            color="white",
            fontsize=9,
            fontweight="bold",
            zorder=4,
        )

    ax.set_xticks(list(x_positions))
    ax.set_xticklabels([r.sheet_id for r in ordered], rotation=45, ha="right")
    ax.set_yticks([-1, 0, 1])
    ax.set_yticklabels(["Absent", "Ambiguous", "Present"])
    ax.set_ylim(-1.6, 1.6)
    ax.set_xlabel("Session (Sheet Identifier)")
    ax.set_ylabel("Status")

    student = ordered[0]
    ax.set_title(f"Attendance timeline — {student.student_name} ({student.student_index})")

    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markersize=10,
            markerfacecolor=_STATUS_STYLE[status]["color"],
            markeredgecolor=_STATUS_STYLE[status]["color"],
            label=f"{_STATUS_STYLE[status]['icon']} {_STATUS_STYLE[status]['label']}",
        )
        for status in _LEGEND_ORDER
    ]
    ax.legend(handles=handles, loc="upper right", frameon=False)

    ax.text(
        0.5,
        -0.5,
        _attendance_rate_caption(ordered),
        transform=ax.transAxes,
        ha="center",
        fontsize=10,
        color="#33383F",
    )

    fig.tight_layout()
    return fig
