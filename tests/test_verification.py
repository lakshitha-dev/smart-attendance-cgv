"""Story 3.3 — evaluate signature verification on the committed protocol split.

Imports `sams_core` only (AD-9): no frontend, no pipeline. Two parts:

1. Engine unit tests — the pure `compare_crops` scorer and every no-data path of
   `verify_signature` (AD-6).
2. The protocol-split evaluation — genuine probes (a student's own sheets 4-5
   crops) vs impostor probes (other students' crops) against the committed
   References (sheets 1-3). It asserts the separation the `SIMILARITY_THRESHOLD`
   in `config.py` relies on and saves the genuine/impostor score-distribution
   figure (with the threshold line) for the report.

## Threshold justification (report-ready)

Similarity = cosine of HOG descriptors on size-normalized binary crops. On the
committed split the genuine mean (~0.44) sits above the impostor mean (~0.33)
with ranked-AUC ~0.74 — real but MODEST separation, exactly the FR-10 risk the
PRD flagged for short, low-texture scribbles. `SIMILARITY_THRESHOLD = 0.40` is
placed at the equal-error operating point of these two distributions: it lets
through most genuine matches while rejecting most impostors, and the residual
overlap either side of the line is reported honestly rather than hidden. Tuning
moves ONLY that one constant, which both `investigate.py` and the Web page read.
"""

import os
from pathlib import Path

import cv2
import numpy as np
import pytest
from matplotlib.figure import Figure

from sams_core import config, verification
from sams_core.models import VerificationOutcome
from sams_core.repository import AttendanceRepository
from sams_core.visualization import render_score_distribution

REFERENCES_DIR = config.REFERENCES_DIR
PROBES_DIR = Path(__file__).resolve().parent / "data" / "probes"
REFERENCE_SHEETS = ("2019-05-31", "2019-06-21", "2019-06-28")
PROBE_SHEETS = ("2019-07-05", "2019-07-12")
INDICES = ("10000409", "10009301", "10009302", "10009303", "10009304", "10009306")

_HAS_FIXTURES = REFERENCES_DIR.is_dir() and PROBES_DIR.is_dir()
_needs_fixtures = pytest.mark.skipif(
    not _HAS_FIXTURES, reason="reference/probe fixtures not present"
)


def _load_gray(path: Path) -> np.ndarray:
    return cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)


def _probe_path(sheet: str, index: str) -> Path:
    return PROBES_DIR / sheet / f"{index}.png"


# --- Pure scorer (compare_crops) ---------------------------------------------


def _synthetic_signature(strokes) -> np.ndarray:
    """White canvas (255) with black ink strokes (0) — the crop shape the
    detector saves. `strokes` is a list of (p1, p2) line endpoints."""
    canvas = np.full((120, 360), 255, dtype=np.uint8)
    for p1, p2 in strokes:
        cv2.line(canvas, p1, p2, 0, 6)
    return canvas


def test_compare_identical_crops_scores_one():
    sig = _synthetic_signature([((20, 20), (300, 100)), ((20, 100), (300, 20))])
    assert verification.compare_crops(sig, sig) == pytest.approx(1.0, abs=1e-6)


def test_compare_score_is_symmetric():
    a = _synthetic_signature([((20, 20), (300, 100))])
    b = _synthetic_signature([((20, 100), (300, 20))])
    assert verification.compare_crops(a, b) == pytest.approx(
        verification.compare_crops(b, a), abs=1e-6
    )


def test_compare_similar_scores_higher_than_dissimilar():
    reference = _synthetic_signature([((20, 20), (320, 100))])
    similar = _synthetic_signature([((20, 24), (320, 104))])  # same orientation, shifted
    dissimilar = _synthetic_signature([((180, 10), (180, 110))])  # vertical stroke
    assert verification.compare_crops(reference, similar) > verification.compare_crops(
        reference, dissimilar
    )


def test_compare_score_never_leaves_zero_to_one():
    a = _synthetic_signature([((20, 20), (300, 100))])
    b = _synthetic_signature([((40, 80), (280, 40)), ((60, 20), (60, 100))])
    for x, y in [(a, a), (a, b), (b, a)]:
        assert 0.0 <= verification.compare_crops(x, y) <= 1.0


def test_compare_blank_crop_scores_zero():
    blank = np.full((120, 360), 255, dtype=np.uint8)  # no ink
    inked = _synthetic_signature([((20, 20), (300, 100))])
    assert verification.compare_crops(blank, inked) == 0.0
    assert verification.compare_crops(inked, blank) == 0.0


# --- verify_signature no-data outcomes (AD-6) --------------------------------


@pytest.fixture
def repo(tmp_path):
    return AttendanceRepository(db_path=tmp_path / "sams.db")


def _seed_student(repo, index="10009301", no="002"):
    from sams_core.models import StudentRecord

    repo.upsert_students([StudentRecord(no=no, index=index, title="Mr", name="Shehan")])


def test_verify_empty_db_is_no_data_not_error(repo):
    result = verification.verify_signature("10009301", repository=repo)
    assert result.outcome is VerificationOutcome.EMPTY_DB
    assert result.best is None


def test_verify_unknown_index_lists_valid_students(repo):
    _seed_student(repo)
    result = verification.verify_signature("99999999", repository=repo)
    assert result.outcome is VerificationOutcome.UNKNOWN
    assert any(s["student_index"] == "10009301" for s in result.valid_students)


def test_verify_ambiguous_ordinal_names_candidates(repo):
    from sams_core.models import StudentRecord

    repo.upsert_students(
        [
            StudentRecord(no="002", index="10009301", title="Mr", name="A"),
            StudentRecord(no="002", index="20000002", title="Ms", name="B"),
        ]
    )
    result = verification.verify_signature("2", repository=repo)
    assert result.outcome is VerificationOutcome.AMBIGUOUS
    assert set(result.candidates) == {"10009301", "20000002"}


def test_verify_known_student_without_references_is_no_data(repo, tmp_path):
    _seed_student(repo)
    empty_refs = tmp_path / "references"  # exists but has no folder for the student
    empty_refs.mkdir()
    result = verification.verify_signature(
        "10009301", repository=repo, references_dir=empty_refs
    )
    assert result.outcome is VerificationOutcome.NO_REFERENCES
    assert result.student_index == "10009301"


@_needs_fixtures
def test_verify_references_present_but_no_probe_is_no_data(repo):
    _seed_student(repo)
    # References exist on the real filesystem, but nothing was processed, so no
    # probe crop is registered.
    result = verification.verify_signature("10009301", repository=repo)
    assert result.outcome is VerificationOutcome.NO_PROBE


@_needs_fixtures
def test_verify_found_returns_best_match_and_verdict(repo):
    _seed_student(repo)
    probe = _probe_path("2019-07-05", "10009301")
    repo.register_signature_image(
        "10009301", "2019-07-05", config.SIGNATURE_KIND_PROBE, probe
    )

    result = verification.verify_signature("10009301", repository=repo)

    assert result.outcome is VerificationOutcome.FOUND
    assert result.probe_sheet_id == "2019-07-05"
    assert len(result.all_scores) == len(REFERENCE_SHEETS)  # 3 references compared
    # Best-match selection happened in the engine: all_scores sorted best-first.
    assert result.best is result.all_scores[0]
    assert result.all_scores == tuple(
        sorted(result.all_scores, key=lambda s: s.score, reverse=True)
    )
    assert result.matched == (result.best.score >= result.threshold)
    assert result.threshold == config.SIMILARITY_THRESHOLD


@_needs_fixtures
def test_verify_both_index_forms_give_identical_result(repo):
    _seed_student(repo)
    repo.register_signature_image(
        "10009301", "2019-07-05", config.SIGNATURE_KIND_PROBE,
        _probe_path("2019-07-05", "10009301"),
    )
    by_short = verification.verify_signature("002", repository=repo)
    by_full = verification.verify_signature("10009301", repository=repo)
    assert by_short.best.score == by_full.best.score
    assert by_short.matched == by_full.matched


@_needs_fixtures
def test_verify_never_compares_a_signature_against_itself(repo):
    """A probe whose sheet is also a reference sheet: that reference is skipped
    (FR-9 disjoint split), so no self-comparison inflates the score."""
    _seed_student(repo)
    repo.register_signature_image(
        "10009301", "2019-05-31", config.SIGNATURE_KIND_PROBE,
        # a reference sheet used as the probe sheet
        REFERENCES_DIR / "10009301" / "2019-05-31.png",
    )
    result = verification.verify_signature("10009301", repository=repo)
    assert result.outcome is VerificationOutcome.FOUND
    assert all(s.sheet_id != "2019-05-31" for s in result.all_scores)
    assert len(result.all_scores) == len(REFERENCE_SHEETS) - 1


# --- Protocol-split evaluation (SM-4) + report figure ------------------------


def _evaluation_scores():
    """Build the genuine/impostor score matrix from the committed split.

    Genuine: each student's own probes (sheets 4-5) vs their References, best
    match. Impostor: every other student's probes vs this student's References,
    best match. Returns (genuine, impostor, per_student) with per-student best
    genuine and best impostor scores for the per-student report."""
    references = {
        idx: [(s, _load_gray(p)) for s, p in verification.load_references(idx, references_dir=REFERENCES_DIR)]
        for idx in INDICES
    }
    probes = {
        idx: [_load_gray(_probe_path(sheet, idx)) for sheet in PROBE_SHEETS]
        for idx in INDICES
    }

    def best(probe, refs):
        return max(verification.compare_crops(probe, ref) for _, ref in refs)

    genuine, impostor, per_student = [], [], {}
    for idx in INDICES:
        own = [best(p, references[idx]) for p in probes[idx]]
        others = [
            best(p, references[idx]) for o in INDICES if o != idx for p in probes[o]
        ]
        genuine.extend(own)
        impostor.extend(others)
        per_student[idx] = (max(own), max(others))
    return np.array(genuine), np.array(impostor), per_student


def _ranked_auc(genuine, impostor) -> float:
    """Probability a random genuine outscores a random impostor (Mann-Whitney)."""
    wins = sum((g > i) + 0.5 * (g == i) for g in genuine for i in impostor)
    return wins / (len(genuine) * len(impostor))


@_needs_fixtures
def test_protocol_split_separates_genuine_from_impostor():
    genuine, impostor, per_student = _evaluation_scores()

    assert len(genuine) == len(INDICES) * len(PROBE_SHEETS)
    assert len(impostor) == len(INDICES) * (len(INDICES) - 1) * len(PROBE_SHEETS)

    # Modest but real separation (honest reporting, FR-10): genuine scores sit
    # above impostor scores on average and by rank.
    assert genuine.mean() > impostor.mean()
    assert _ranked_auc(genuine, impostor) >= 0.65

    threshold = config.SIMILARITY_THRESHOLD
    genuine_matched = (genuine >= threshold).mean()
    impostor_rejected = (impostor < threshold).mean()
    # At the chosen threshold the majority on each side is classified correctly.
    assert genuine_matched >= 0.6
    assert impostor_rejected >= 0.6


@_needs_fixtures
def test_score_distribution_figure_saved_for_report(tmp_path, monkeypatch):
    genuine, impostor, _ = _evaluation_scores()
    fig = render_score_distribution(genuine, impostor, config.SIMILARITY_THRESHOLD)
    assert isinstance(fig, Figure)

    out_dir = config.OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "verification_score_distribution.png"
    fig.savefig(out_path)
    assert out_path.is_file() and out_path.stat().st_size > 0


@_needs_fixtures
def test_per_student_verdicts_reported():
    """Per-student separation is reported (SM-4): for most students the best
    genuine score beats their best impostor score. Modest overlap is expected
    and documented rather than asserted away."""
    _, _, per_student = _evaluation_scores()
    separated = sum(1 for g, i in per_student.values() if g > i)
    assert separated >= len(INDICES) // 2
