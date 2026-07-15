# ground_truth.csv — provenance and rules

- **What:** the SM-1 answer key — one row per (Signing Sheet, Student Index) across all
  five sample sheets: `status ∈ {Present, Absent, Disputed}`. Disputed rows are excluded
  from SM-1 scoring and reported separately (PRD §7).
- **Adjudicated:** 2026-07-13, by visual inspection of `sample_signin-sheets/1..5.jpeg`,
  **before** any detection-threshold tuning (PRD §6.3 / AD-9 ordering rule). The team
  should ratify it; change it only by re-adjudication, never to make a test pass.
- **Straddle notes:** sheet 2019-06-21 rows 2–3 and sheets 2019-05-31 / 2019-07-12 contain
  signatures drawn high/overlapping adjacent rows — attributed per PRD FR-4's
  one-cell-per-component rule.
- **Format:** plain CSV, header first, no comment lines — safe for `csv.DictReader`
  and `pandas.read_csv` without special options (Story 1.6's harness relies on this).
