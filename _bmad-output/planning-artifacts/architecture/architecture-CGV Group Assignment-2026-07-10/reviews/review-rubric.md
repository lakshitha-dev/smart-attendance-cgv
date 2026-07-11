---
title: Rubric Review — ARCHITECTURE-SPINE.md (SAMS)
reviewer: rubric-walker
reviewed: 2026-07-10
target: ../ARCHITECTURE-SPINE.md
verdict: pass-with-fixes
---

# Rubric Review — Architecture Spine (SAMS)

**Verdict: pass-with-fixes.** The spine is a genuinely strong build substrate: eleven ADs that each target a real 10-author divergence point, an executable success-metric gate, verified-current tech, full FR coverage, and a terse voice. The fixes are small and surgical — two half-specified seams (Student Index resolution ownership, the operator-resolution write API) and two minor silent states.

---

## Rubric walk

### 1. Fixes the real divergence points for the level below — MOSTLY, two gaps

The eleven ADs hit the divergences that would actually bite 10 students + AI agents writing stories in parallel:

- Engine/frontend boundary (AD-1), typed contracts (AD-2), single stage registry (AD-3), sole DB gateway with overwrite semantics (AD-4), config ownership with the SM-C1 anti-overfitting bind (AD-5), error strategy with exit codes and the warnings-vs-exceptions split (AD-6), display boundary (AD-7), dependency isolation protecting the graded install path (AD-8), executable SM gate + disjoint verification split (AD-9), signature storage layout (AD-10), Sheet Identifier resolution chain (AD-11). Each names the divergence it prevents, and each would in fact prevent it.
- AD-2's `SheetResult.warnings` + AD-6's "anomalies are warnings, never exceptions" correctly encodes the UX's "row-count mismatch is a flag, not a failure" — a spot where two authors would otherwise have split.
- AD-4's `has_operator_resolutions(sheet_id)` pre-Process read shows the spine actually walked the UX overwrite-warning flow.

**Gap 1 — Student Index dual-form resolution has no owning module (MEDIUM).** Consistency Conventions demands "Student Index resolves both 8-digit and short-alias forms everywhere an index is accepted" (PRD §3, FR-7/FR-10/FR-14), but no AD assigns the resolver a home. Consumers: `infovis.py`, `investigate.py`, webui Lookup, webui Investigate, and repository queries. AD-1 pushes logic into `sams_core`, but *where* in the core is undecided — two story authors can plausibly put alias resolution in `repository.py` and in `models.py` (or worse, once per adapter), with divergent edge behavior (zero-padding, is `2` valid for `002`, unknown-alias handling). Fix: one sentence in AD-4 (or AD-2) naming a single resolver, e.g. `repository.resolve_student_index(raw) -> StudentRecord | None`.

**Gap 2 — operator-resolution write API is unnamed (LOW-MEDIUM).** AD-4 names the read APIs (`list_students`, `has_operator_resolutions`) and the upsert, but the write the Web UI Ambiguous-resolve story needs — resolve to Present/Absent setting `resolved_by_operator`, plus Undo restoring Ambiguous (UX Component Patterns) — is only implied. Divergence is bounded (repository.py is the only sqlite3 importer), but the API surface is half-specified where it was fully specified for reads. Fix: add the resolve/undo signature to AD-4's rule.

### 2. Every AD's Rule is enforceable — PASS

Each Rule is mechanically checkable: "only module importing sqlite3", "entry scripts <50 lines", "no numeric literals in stage/verification code", "never imports streamlit", "tests import sams_core only", exit codes 0/2/1, "references from sheets 1–3, probes from 4–5". Nothing is a vibe. The Prevents lines match the Rules — no rule that fails to block its stated divergence.

Minor: AD-7's CLI rendering clause ("OpenCV windows + per-student stdout summary") describes only `sams.py`; how `infovis.py`/`investigate.py` adapters display the returned `Figure` (`plt.show()` in the adapter) is implied by "visualization.py returns Figure objects" but never stated (LOW).

### 3. Nothing under Deferred could let two units diverge — PASS

Each deferral sits behind a named seam: stage algorithms behind AD-3's pure-function contract, similarity internals behind `VerificationResult`, session-state keys inside `webui/`, logging with a stated default that stands until overridden, Info File evolution isolated in `info_file.py`, packaging trivially ZIP. No deferral leaks across a unit boundary.

### 4. Named tech verified-current — PASS (verified independently)

Checked 2026-07-10 against PyPI: opencv-python **5.0.0.93** (released 2026-07-02) and streamlit **1.59.1** (released 2026-07-08) are both the current latest — the spine's claim of same-day web verification holds. The opencv 5.x pin is hedged with an explicit [ASSUMPTION] and a 4.12.x fallback naming the exact API surface at risk — good. Note (LOW/INFO): 5.0.0.93 was one week old at spine time; for graded coursework where lab material likely targets 4.x, defaulting to 4.12.x and treating 5.x as the upgrade would be the safer inversion. numpy 2.5.1 / matplotlib 3.11.x are consistent with the same date; pytest deliberately unpinned (dev-only) is fine.

### 5. Covers the driving spec's capabilities (FR-1..16) — PASS

The Capability → Architecture Map accounts for every FR-1..FR-16, each with a home module and governing AD(s); SM-1..SM-5 are bound through AD-9 and the frontmatter binds. Cross-checked against the PRD: no FR is silently dropped, and the UX-added obligations (overwrite semantics, Ambiguous first-class, per-sheet output folders, one-shot Process fence, no-data state) all appear in Inherited Invariants or ADs.

One silent state (LOW): **probe availability sequencing.** AD-10 makes `investigate.py`'s probes the crops saved while processing sheets 4–5. On a fresh machine, `investigate.py 001` before those sheets are processed has no probe — AD-6 specifies unknown-index behavior but not the known-index/no-probe state, so CLI and Web could diverge on it (error vs no-data). One clause in AD-6 or AD-10 settles it.

### 6. Every owned dimension decided, deferred, or open — PASS

The Operational Envelope section exists and is substantive: runtime targets (student machines + grader fresh machine), no cloud, CI explicitly not mandated, Web UI transport (`streamlit run`, localhost/LAN), build sequencing (gate + ground-truth-before-tuning), and deliverable packaging (LMS ZIP structure). Security/auth is decided by the inherited stack fence. Logging has a default. No whole dimension is silent. (Team git/branching workflow for 10 contributors is absent, but that is legitimately epics-phase process, not architecture — PRD §6.3 already defers decomposition there.)

### 7. Terse, valid mermaid, no template residue — PASS

Both mermaid blocks parse (quoted labels, cylinder shapes, HTML-escaped `<>` in the FS node). Rules carry a one-line Prevents each — structural, not rationale bloat. No template comments, no placeholders; `[ASSUMPTION]` tags are load-bearing, not residue. The frontmatter still says `status: draft` — flip to final when the fixes land.

---

## Findings summary

| # | Severity | Finding | Fix |
|---|----------|---------|-----|
| 1 | Medium | Dual-form Student Index resolution required "everywhere" but no module owns the resolver — 5 consumers can implement it 5 ways | Name one engine resolver in AD-4/AD-2, e.g. `repository.resolve_student_index()` |
| 2 | Low-Medium | AD-4 omits the operator-resolution write API (resolve + Undo restoring Ambiguous) that the Web UI story needs | Add resolve/undo signature to AD-4 |
| 3 | Low | Known-index-but-no-probe state for `investigate.py` unspecified (probes only exist after sheets 4–5 are processed) — CLI/Web could diverge | One clause in AD-6 or AD-10 defining the no-probe result |
| 4 | Low | AD-7 states CLI rendering for `sams.py` only; Figure display for `infovis.py`/`investigate.py` adapters is implied, not stated | Add "graph/verdict adapters call `plt.show()`/print in the adapter" to AD-7 |
| 5 | Info | opencv-python 5.0.0.93 pin is one week old at spine date; hedge exists but 4.12.x-as-default is the safer coursework posture | Optional: invert default and fallback |

**Verdict: pass-with-fixes** — apply findings 1–2 before epics/stories are cut; 3–5 can ride along.

Sources for version verification: [opencv-python on PyPI](https://pypi.org/project/opencv-python/), [opencv-python releases](https://github.com/opencv/opencv-python/releases), [streamlit on PyPI](https://pypi.org/project/streamlit/).
