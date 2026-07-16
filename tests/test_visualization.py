import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from sams_core.models import AttendanceRecord, AttendanceStatus
from sams_core.visualization import render_attendance_timeline


def _record(sheet_id, status):
    return AttendanceRecord(
        student_index="10000409",
        student_name="Alice",
        sheet_id=sheet_id,
        status=status,
        subject_code="CS402.3",
        subject_name="Computer Graphics",
    )


def _multi_session_records():
    return [
        _record("2019-05-31", AttendanceStatus.PRESENT),
        _record("2019-06-07", AttendanceStatus.ABSENT),
        _record("2019-06-14", AttendanceStatus.AMBIGUOUS),
        _record("2019-06-21", AttendanceStatus.PRESENT),
    ]


def test_render_attendance_timeline_returns_figure_never_shows(monkeypatch):
    shown = []
    monkeypatch.setattr(plt, "show", lambda *a, **k: shown.append(True))

    fig = render_attendance_timeline(_multi_session_records())

    assert isinstance(fig, Figure)
    assert shown == []


def test_render_attendance_timeline_one_mark_per_session():
    records = _multi_session_records()

    fig = render_attendance_timeline(records)
    ax = fig.axes[0]
    scatter = ax.collections[0]

    assert len(scatter.get_offsets()) == len(records)


def test_render_attendance_timeline_ambiguous_is_a_distinct_mid_band():
    fig = render_attendance_timeline(_multi_session_records())
    ax = fig.axes[0]
    scatter = ax.collections[0]
    ys = [point[1] for point in scatter.get_offsets()]

    # Sorted by sheet_id: Present, Absent, Ambiguous, Present.
    present_y = [ys[0], ys[3]]
    absent_y = ys[1]
    ambiguous_y = ys[2]

    assert present_y[0] == present_y[1]
    assert ambiguous_y != absent_y
    assert ambiguous_y != present_y[0]
    assert min(present_y[0], absent_y) < ambiguous_y < max(present_y[0], absent_y)


def test_render_attendance_timeline_status_colours_match_ux_spec():
    fig = render_attendance_timeline(_multi_session_records())
    ax = fig.axes[0]
    scatter = ax.collections[0]
    colours = [tuple(c) for c in scatter.get_facecolor()]

    import matplotlib.colors as mcolors

    present = mcolors.to_rgba("#256E4C")
    absent = mcolors.to_rgba("#A63D2A")
    ambiguous = mcolors.to_rgba("#7A6212")

    assert colours[0] == present  # 2019-05-31 Present
    assert colours[1] == absent  # 2019-06-07 Absent
    assert colours[2] == ambiguous  # 2019-06-14 Ambiguous
    assert colours[3] == present  # 2019-06-21 Present


def test_render_attendance_timeline_legend_carries_icon_and_text_per_status():
    fig = render_attendance_timeline(_multi_session_records())
    ax = fig.axes[0]
    legend = ax.get_legend()
    labels = {text.get_text() for text in legend.get_texts()}

    assert any("Present" in label and "✓" in label for label in labels)
    assert any("Absent" in label and "✕" in label for label in labels)
    assert any("Ambiguous" in label and "?" in label for label in labels)


def test_render_attendance_timeline_has_title_and_axis_labels():
    fig = render_attendance_timeline(_multi_session_records())
    ax = fig.axes[0]

    assert ax.get_title() != ""
    assert ax.get_xlabel() != ""
    assert ax.get_ylabel() != ""
    assert "Alice" in ax.get_title() or "10000409" in ax.get_title()


def test_render_attendance_timeline_annotates_attendance_rate_excluding_ambiguous():
    # 2 Present, 1 Absent, 1 Ambiguous -> rate over the 3 counted sessions.
    fig = render_attendance_timeline(_multi_session_records())
    ax = fig.axes[0]

    all_text = " ".join(t.get_text() for t in ax.texts) + ax.get_title()
    assert "%" in all_text
    assert "67" in all_text  # 2/3 = 66.7%, rounds to 67
    assert "pending" in all_text.lower() or "1" in all_text
