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


def _all_figure_text(fig):
    ax = fig.axes[0]
    return (
        " ".join(t.get_text() for t in ax.texts)
        + " ".join(t.get_text() for t in fig.texts)
        + ax.get_title()
    )


def test_render_attendance_timeline_annotates_attendance_rate_excluding_ambiguous():
    # 2 Present, 1 Absent, 1 Ambiguous -> rate over the 3 counted sessions.
    fig = render_attendance_timeline(_multi_session_records())

    all_text = _all_figure_text(fig)
    assert "%" in all_text
    assert "67" in all_text  # 2/3 = 66.7%, rounds to 67
    assert "pending" in all_text.lower() or "1" in all_text


def test_render_attendance_timeline_empty_records_raise_typed_error():
    """The renderer is a public engine API: an empty query result must fail
    with the engine's own error type, never a raw IndexError."""
    import pytest

    from sams_core.errors import InputError

    with pytest.raises(InputError):
        render_attendance_timeline([])


def test_render_attendance_timeline_all_ambiguous_rate_is_na_not_zero():
    """An all-Ambiguous student must never be branded '0% attendance'."""
    fig = render_attendance_timeline(
        [
            _record("2019-05-31", AttendanceStatus.AMBIGUOUS),
            _record("2019-06-07", AttendanceStatus.AMBIGUOUS),
        ]
    )
    all_text = _all_figure_text(fig)
    assert "n/a" in all_text
    assert "0%" not in all_text


def test_render_attendance_timeline_legend_sits_above_the_data_band():
    """The legend must never occlude markers: it lives in the headroom above
    y=1 (Present), so the most recent marks stay visible."""
    fig = render_attendance_timeline(_multi_session_records())
    ax = fig.axes[0]
    assert ax.get_ylim()[1] > 1.5  # reserved headroom exists
    legend_y0 = ax.get_legend().get_window_extent(fig.canvas.get_renderer()).y0
    present_marker_y = ax.transData.transform((0, 1))[1]
    assert legend_y0 > present_marker_y


def test_render_attendance_timeline_yticks_derive_from_status_mapping():
    from sams_core.visualization import _STATUS_STYLE

    fig = render_attendance_timeline(_multi_session_records())
    ax = fig.axes[0]
    tick_to_label = dict(zip(ax.get_yticks(), [t.get_text() for t in ax.get_yticklabels()]))
    for style in _STATUS_STYLE.values():
        assert tick_to_label[style["y"]] == style["label"]


def test_render_attendance_timeline_non_iso_sheet_ids_sort_after_dated_ones():
    records = [
        _record("IMG_5031", AttendanceStatus.PRESENT),
        _record("2019-06-07", AttendanceStatus.ABSENT),
        _record("2019-05-31", AttendanceStatus.PRESENT),
    ]
    fig = render_attendance_timeline(records)
    ax = fig.axes[0]
    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert labels == ["2019-05-31", "2019-06-07", "IMG_5031"]
