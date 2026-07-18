"""Signature verification engine (Epic 3, FR-9/FR-10, AD-9).

`verify_signature` is the ONE comparison API both frontends call — the CLI
(`investigate.py`) and the Web Investigate page (Story 4.6) each pass a Student
Index (either form) and render the returned `VerificationResult`; neither
re-implements the match logic. Best-match selection over multiple Reference
Signatures happens HERE, inside the engine.

Data model (AD-10, no image blobs anywhere):
- Reference Signatures live on the FILESYSTEM under `references/<student_index>/`,
  one image per known-good sample, hand-curated by the team from sheets 1-3.
  Each file is named by its source Sheet Identifier (e.g. `2019-05-31.png`) so
  the disjoint reference/probe split (SM-4) is provable from the filename alone.
- Probe crops are the per-student signature cells Story 1.4 saves to
  `output/<sheet>/crops/<index>.png` and Story 1.5 registers in the Local DB as
  `kind="probe"` paths. The most recently processed sheet is taken as the probe.

Comparison method (the Day-6 spike, documented honestly per FR-10):
- Normalize each crop: binarize (crops arrive near-binary already), drop specks,
  crop to the ink bounding box, then fit — aspect-preserving and centered — into
  a fixed HOG window.
- Describe it with a Histogram of Oriented Gradients (HOG): this captures the
  stroke-orientation structure of a signature, which is more robust on these
  short, low-texture scribbles than raw ORB/SIFT keypoint matching (the PRD's
  flagged FR-10 risk — classic feature matching separates these poorly).
- Score = cosine similarity of the two HOG vectors. HOG vectors are
  non-negative, so cosine already lands in [0, 1] with HIGHER = more similar
  (AD-9); no distance-to-similarity inversion is needed.
- `matched = score >= config.SIMILARITY_THRESHOLD`. The threshold is the single
  named constant both frontends read; its value is justified against the split's
  score distributions in `tests/test_verification.py` and the report.

Score separation on the protocol split is modest (AUC ~0.74): honest, and the
brief credits the documented attempt. This module never imports a UI framework
and never prints/exits (AD-6) — adapters own all presentation.
"""

from pathlib import Path

import cv2
import numpy as np

from sams_core import config
from sams_core.models import (
    ReferenceScore,
    VerificationOutcome,
    VerificationResult,
)
from sams_core.repository import AttendanceRepository

# The HOG descriptor is stateless and immutable once built — construct it once
# and reuse it across every comparison in the process.
_hog: cv2.HOGDescriptor | None = None


def _hog_descriptor() -> cv2.HOGDescriptor:
    global _hog
    if _hog is None:
        win = (config.VERIFY_NORMALIZED_WIDTH, config.VERIFY_NORMALIZED_HEIGHT)
        block = (config.VERIFY_HOG_BLOCK_PX, config.VERIFY_HOG_BLOCK_PX)
        stride = (config.VERIFY_HOG_STRIDE_PX, config.VERIFY_HOG_STRIDE_PX)
        cell = (config.VERIFY_HOG_CELL_PX, config.VERIFY_HOG_CELL_PX)
        _hog = cv2.HOGDescriptor(win, block, stride, cell, config.VERIFY_HOG_ORIENTATION_BINS)
    return _hog


def _load_gray(path: str | Path) -> np.ndarray | None:
    """Read an image as greyscale, or None if the file is missing/unreadable.

    Uses np.fromfile + imdecode (not cv2.imread) so non-ASCII Windows paths load,
    matching `image_io.py`. A missing or corrupt file is a no-data condition
    (AD-6), never an exception past the engine boundary.
    """
    file_path = Path(path)
    if not file_path.is_file():
        return None
    data = np.fromfile(str(file_path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)


def _ink_bounding_box(gray: np.ndarray) -> np.ndarray | None:
    """Binarize a crop to its ink mask and tighten to the ink's bounding box.

    Returns a uint8 mask (ink = 255) cropped to the signature, or None when the
    crop holds no ink above the speck floor — an empty cell can't be normalized
    or scored.
    """
    _, binary = cv2.threshold(
        gray, config.VERIFY_BINARY_THRESHOLD, 255, cv2.THRESH_BINARY_INV
    )
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    kept = np.zeros_like(binary)
    for label in range(1, num_labels):  # label 0 is background
        if stats[label, cv2.CC_STAT_AREA] >= config.VERIFY_MIN_INK_COMPONENT_AREA_PX:
            kept[labels == label] = 255

    ys, xs = np.nonzero(kept)
    if xs.size == 0:
        return None
    return kept[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]


def _hog_features(gray: np.ndarray) -> np.ndarray | None:
    """Normalize a crop and return its HOG feature vector, or None if it has no ink.

    The ink bounding box is fitted into the fixed HOG window aspect-preserving
    and centered (padded with background), so two signatures of different sizes
    or positions in their cells still line up for comparison.
    """
    binary = _ink_bounding_box(gray)
    if binary is None:
        return None

    target_w = config.VERIFY_NORMALIZED_WIDTH
    target_h = config.VERIFY_NORMALIZED_HEIGHT
    height, width = binary.shape
    scale = min(target_w / width, target_h / height)
    resized = cv2.resize(
        binary,
        (max(1, int(round(width * scale))), max(1, int(round(height * scale)))),
        interpolation=cv2.INTER_AREA,
    )

    canvas = np.zeros((target_h, target_w), dtype=np.uint8)
    y_offset = (target_h - resized.shape[0]) // 2
    x_offset = (target_w - resized.shape[1]) // 2
    canvas[y_offset : y_offset + resized.shape[0], x_offset : x_offset + resized.shape[1]] = resized

    return _hog_descriptor().compute(canvas).ravel()


def compare_crops(probe_gray: np.ndarray, reference_gray: np.ndarray) -> float:
    """Similarity of two greyscale signature crops, 0-1, HIGHER = more similar (AD-9).

    Pure and headless — the unit under test in Story 3.3. Returns 0.0 (least
    similar) when either crop is empty of ink, so a blank cell never scores as a
    confident match.
    """
    probe = _hog_features(probe_gray)
    reference = _hog_features(reference_gray)
    if probe is None or reference is None:
        return 0.0

    denominator = float(np.linalg.norm(probe) * np.linalg.norm(reference))
    if denominator == 0.0:
        return 0.0
    score = float(np.dot(probe, reference) / denominator)
    # HOG vectors are non-negative so cosine is already in [0, 1]; clamp only to
    # absorb floating-point drift at the extremes.
    return max(0.0, min(1.0, score))


def load_references(
    student_index: str,
    repository: AttendanceRepository | None = None,
    references_dir: str | Path | None = None,
) -> list[tuple[str, Path]]:
    """Reference Signatures for a canonical Student Index (Story 3.1, AD-10).

    Returns (sheet_id, path) pairs sorted by filename, where `sheet_id` is the
    file's stem (its source Sheet Identifier — the provenance manifest, SM-4).
    An empty or missing `references/<index>/` folder yields `[]` — a no-data
    result, never an exception (AD-6).

    Dropping image files into the folder is the complete ingestion path: when a
    `repository` is given, each reference's PATH (never its bytes) is registered
    in the Local DB on read, satisfying the "register on first use" contract.
    Registration is idempotent; the filesystem remains the source of truth, so
    the DB copy is self-healing if `persist_run` later clears a same-dated row.
    """
    base = Path(references_dir) if references_dir is not None else config.REFERENCES_DIR
    folder = base / student_index
    if not folder.is_dir():
        return []

    references = [
        (path.stem, path)
        for path in sorted(folder.iterdir())
        if path.is_file() and path.suffix.lower() in config.REFERENCE_IMAGE_EXTENSIONS
    ]

    if repository is not None:
        for sheet_id, path in references:
            repository.register_signature_image(
                student_index, sheet_id, config.SIGNATURE_KIND_REFERENCE, path
            )
    return references


def _latest_probe(
    repository: AttendanceRepository, student_index: str
) -> tuple[str, str] | None:
    """The most recently processed sheet's probe crop for a student (Story 3.2).

    Probe registrations are ordered by Sheet Identifier, so the last one is the
    latest sheet — 'the signature captured from the sheet' the operator wants to
    check. None when the student has no registered probe crop yet.
    """
    probes = repository.get_signature_images(student_index, config.SIGNATURE_KIND_PROBE)
    return probes[-1] if probes else None


def verify_signature(
    alias: str,
    repository: AttendanceRepository | None = None,
    references_dir: str | Path | None = None,
) -> VerificationResult:
    """Compare a student's probe signature against their References (FR-10, AD-9).

    Resolves `alias` (either index form) via the ONE repository resolver, loads
    the student's Reference Signatures and their latest probe crop, scores the
    probe against every reference, and returns a `VerificationResult` whose
    `best`/`matched`/`threshold` the frontends render verbatim. A reference from
    the SAME sheet as the probe is skipped so no signature is ever compared
    against itself (FR-9 protocol). Every no-data shape is a typed outcome, never
    an exception (AD-6): empty DB, ambiguous ordinal, unknown index, no
    References, or no probe crop.
    """
    repo = repository if repository is not None else AttendanceRepository()
    threshold = config.SIMILARITY_THRESHOLD

    index, candidates, roster = repo.resolve_with_roster(alias)
    if not roster:
        return VerificationResult(
            alias=alias, outcome=VerificationOutcome.EMPTY_DB, threshold=threshold
        )
    if candidates:
        return VerificationResult(
            alias=alias,
            outcome=VerificationOutcome.AMBIGUOUS,
            candidates=candidates,
            valid_students=roster,
            threshold=threshold,
        )
    # `index is None` is an unresolvable short ordinal; an UNKNOWN 8-digit form
    # passes resolution through unchanged (repository contract), so also treat a
    # resolved index absent from the roster as unknown — same no-data family
    # (AD-6), mirroring `query_attendance`.
    known = {s["student_index"]: s["name"] for s in roster}
    if index is None or index not in known:
        return VerificationResult(
            alias=alias,
            outcome=VerificationOutcome.UNKNOWN,
            valid_students=roster,
            threshold=threshold,
        )

    name = known[index]

    references = load_references(index, repository=repo, references_dir=references_dir)
    if not references:
        return VerificationResult(
            alias=alias,
            outcome=VerificationOutcome.NO_REFERENCES,
            student_index=index,
            student_name=name,
            threshold=threshold,
        )

    probe = _latest_probe(repo, index)
    probe_gray = _load_gray(probe[1]) if probe is not None else None
    if probe is None or probe_gray is None:
        return VerificationResult(
            alias=alias,
            outcome=VerificationOutcome.NO_PROBE,
            student_index=index,
            student_name=name,
            threshold=threshold,
        )
    probe_sheet_id, probe_path = probe

    scores: list[ReferenceScore] = []
    for sheet_id, reference_path in references:
        if sheet_id == probe_sheet_id:
            continue  # never compare a signature against itself (FR-9 disjoint split)
        reference_gray = _load_gray(reference_path)
        if reference_gray is None:
            continue
        scores.append(
            ReferenceScore(
                reference_path=str(reference_path),
                sheet_id=sheet_id,
                score=compare_crops(probe_gray, reference_gray),
            )
        )

    if not scores:
        # Every reference was unreadable or was the probe's own sheet: there is
        # nothing trustworthy left to compare against (no-data, not an error).
        return VerificationResult(
            alias=alias,
            outcome=VerificationOutcome.NO_REFERENCES,
            student_index=index,
            student_name=name,
            probe_path=str(probe_path),
            probe_sheet_id=probe_sheet_id,
            threshold=threshold,
        )

    scores.sort(key=lambda s: s.score, reverse=True)
    best = scores[0]
    return VerificationResult(
        alias=alias,
        outcome=VerificationOutcome.FOUND,
        student_index=index,
        student_name=name,
        probe_path=str(probe_path),
        probe_sheet_id=probe_sheet_id,
        best=best,
        all_scores=tuple(scores),
        matched=best.score >= threshold,
        threshold=threshold,
    )
