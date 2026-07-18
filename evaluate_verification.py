#!/usr/bin/env python
"""Signature-verification evaluation for the report (Story 3.3, SM-4).

Runs the committed protocol split — References from sheets 1-3, genuine probes
from a student's own sheets 4-5, impostor probes from other students — through
the same engine `investigate.py` uses, prints a per-student verdict table with
overall separation, and saves the genuine/impostor score-distribution figure
(with the threshold line) for the report.

This is a thin evaluation harness over `sams_core` (AD-9): it never re-implements
the comparison or the threshold — both come from the engine and `config.py`.

Usage:
    python evaluate_verification.py
    python evaluate_verification.py --probes-dir tests/data/probes --out output
"""
import sys
from argparse import ArgumentParser
from pathlib import Path

import cv2
import numpy as np

from sams_core import config
from sams_core.verification import compare_crops, load_references
from sams_core.visualization import render_score_distribution

PROBE_SHEETS = ("2019-07-05", "2019-07-12")  # the FR-9 probe sheets (4-5)


def _load_gray(path: Path) -> np.ndarray | None:
    if not path.is_file():
        return None
    return cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)


def _student_indices(references_dir: Path) -> list[str]:
    """Every student with a References folder, in index order."""
    if not references_dir.is_dir():
        return []
    return sorted(p.name for p in references_dir.iterdir() if p.is_dir())


def _best_score(probe, references) -> float:
    """Best-match score of a probe against a list of loaded reference crops."""
    return max((compare_crops(probe, ref) for ref in references), default=0.0)


def _ranked_auc(genuine, impostor) -> float:
    """P(random genuine outscores random impostor) — the Mann-Whitney statistic."""
    if not len(genuine) or not len(impostor):
        return float("nan")
    wins = sum((g > i) + 0.5 * (g == i) for g in genuine for i in impostor)
    return wins / (len(genuine) * len(impostor))


def evaluate(references_dir: Path, probes_dir: Path):
    """Return (genuine, impostor, per_student rows) for the protocol split."""
    indices = _student_indices(references_dir)
    references = {
        idx: [
            gray
            for gray in (_load_gray(p) for _, p in load_references(idx, references_dir=references_dir))
            if gray is not None
        ]
        for idx in indices
    }
    probes = {
        idx: [
            gray
            for gray in (_load_gray(probes_dir / sheet / f"{idx}.png") for sheet in PROBE_SHEETS)
            if gray is not None
        ]
        for idx in indices
    }

    genuine, impostor, rows = [], [], []
    for idx in indices:
        own = [_best_score(p, references[idx]) for p in probes[idx]]
        others = [
            _best_score(p, references[idx])
            for other in indices
            if other != idx
            for p in probes[other]
        ]
        genuine.extend(own)
        impostor.extend(others)
        best_genuine = max(own) if own else float("nan")
        best_impostor = max(others) if others else float("nan")
        rows.append((idx, best_genuine, best_impostor, best_genuine > best_impostor))
    return np.array(genuine, dtype=float), np.array(impostor, dtype=float), rows


def main(argv: list[str] | None = None) -> int:
    parser = ArgumentParser(prog="evaluate_verification.py")
    parser.add_argument("--references-dir", default=str(config.REFERENCES_DIR))
    parser.add_argument(
        "--probes-dir",
        default=str(Path(__file__).resolve().parent / "tests" / "data" / "probes"),
    )
    parser.add_argument("--out", default=str(config.OUTPUT_DIR))
    args = parser.parse_args(argv)

    references_dir = Path(args.references_dir)
    probes_dir = Path(args.probes_dir)
    threshold = config.SIMILARITY_THRESHOLD

    genuine, impostor, rows = evaluate(references_dir, probes_dir)
    if not len(genuine) or not len(impostor):
        print(
            "No scores computed — check that references/ and the probes dir are "
            f"populated (references_dir={references_dir}, probes_dir={probes_dir}).",
            file=sys.stderr,
        )
        return 1

    disp = lambda s: round(s * 100)
    print(f"Threshold (config.SIMILARITY_THRESHOLD): {threshold:.2f}  ({disp(threshold)}/100)")
    print()
    print(f"{'Student':<12}{'best genuine':>14}{'best impostor':>16}{'verdict':>12}")
    print("-" * 54)
    for idx, best_g, best_i, separated in rows:
        verdict = "separated" if separated else "OVERLAP"
        print(f"{idx:<12}{disp(best_g):>14}{disp(best_i):>16}{verdict:>12}")
    print("-" * 54)
    print(
        f"genuine  n={len(genuine)}  mean={disp(genuine.mean())}  "
        f"range={disp(genuine.min())}-{disp(genuine.max())}"
    )
    print(
        f"impostor n={len(impostor)}  mean={disp(impostor.mean())}  "
        f"range={disp(impostor.min())}-{disp(impostor.max())}"
    )
    print(f"ranked AUC (genuine vs impostor): {_ranked_auc(genuine, impostor):.3f}")
    print(
        f"at threshold {disp(threshold)}: genuine matched "
        f"{(genuine >= threshold).sum()}/{len(genuine)}, impostor rejected "
        f"{(impostor < threshold).sum()}/{len(impostor)}"
    )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    figure_path = out_dir / "verification_score_distribution.png"
    figure = render_score_distribution(genuine, impostor, threshold)
    figure.savefig(figure_path)
    print(f"\nScore-distribution figure saved to {figure_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
