# ground_truth.csv — provenance and rules

- **What:** the SM-1 answer key — one row per (Signing Sheet, Student Index) across all
  five sample sheets: `status ∈ {Present, Absent, Disputed}`. Disputed rows are excluded
  from SM-1 scoring and reported separately (PRD §7).
- **Adjudicated:** 2026-07-13, by visual inspection of `sample_signin-sheets/1..5.jpeg`,
  in the working tree **before** any detection-threshold tuning (PRD §6.3 / AD-9
  ordering rule). Committed 2026-07-16 as commit `069f99d`, immediately ahead of the
  tuned constants (`0436aee`) — the adjudicate-before-tune ordering is attested by this
  record and the commit sequence, not independently provable from timestamps. The team
  should ratify it; change it only by re-adjudication, never to make a test pass.
- **Straddle notes (reconciled 2026-07-16):** several signatures are drawn high enough
  to touch or cross the printed rule above their row — most visibly on sheets
  2019-05-31, 2019-06-21, and 2019-07-12 (rows 1–3 area), and on 2019-07-05 where row 3's
  signature crosses the row 2/3 rule (it belongs to row 3; the same student signs
  identically on sheets 1, 2, 5). Attribution follows PRD FR-4's one-cell-per-component
  rule. Both adjudications agree on every status regardless of these prose observations.
- **Format:** plain CSV, header first, no comment lines — safe for `csv.DictReader`
  and `pandas.read_csv` without special options (Story 1.6's harness relies on this).
- **Independently re-adjudicated** during Story 1.6 (sprint-5) — both adjudications
  agree on all 30 rows. Sprint-5's per-sheet notes, kept here verbatim:
  - 2019-05-31 (1.jpeg) — all six rows carry a signature.
  - 2019-06-21 (2.jpeg) — all six rows carry a signature.
  - 2019-06-28 (3.jpeg) — rows 2 and 3 are empty; the remaining four are signed.
  - 2019-07-05 (4.jpeg) — row 2 is empty; row 4 holds only a faint speck of pink ink,
    no stroke, adjudicated Absent. Row 3's signature is drawn high and crosses the
    row 2/3 rule — it belongs to row 3 (same student signs identically on sheets 1, 2, 5).
  - 2019-07-12 (5.jpeg) — all six rows carry a signature.
  - No row was judged Disputed: every cell on all five sheets is unambiguous to the eye.
