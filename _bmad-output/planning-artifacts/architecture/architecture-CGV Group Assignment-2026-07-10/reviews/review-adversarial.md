---
title: Adversarial Review — SAMS Architecture Spine
review-type: adversarial (two-units-build-incompatibly lens)
target: ../ARCHITECTURE-SPINE.md
context:
  - ../../../prds/prd-CGV Group Assignment-2026-07-10/prd.md
  - ../../../ux-designs/ux-CGV Group Assignment-2026-07-10/EXPERIENCE.md
verdict: pass-with-fixes
reviewed: 2026-07-10
---

# Adversarial Review — SAMS Architecture Spine

**Lens:** For each finding I play two students, each building one unit one level down, each obeying every AD *to the letter* — and show how their units still refuse to compose. Every pair is a hole; every hole gets the one sentence that would have closed it.

**Verdict: pass-with-fixes.** The spine's boundaries (AD-1, AD-4, AD-7, AD-8) are genuinely hard to violate, and the StageArtifact/models.py contract idea is right. But the contracts it names are under-specified in exactly the places ten parallel authors will diverge: pixel semantics, score direction, generator side-effects, key canonicalization, connection lifetime, and reference-set ownership. All fixes are one-sentence tightenings to existing ADs plus two new ADs — no structural rework.

---

## F-1 (CRITICAL) — `StageArtifact.image`: BGR vs RGB, dtype, channel count are all unspecified

**Unit A — `pipeline.py` (student 1):** Stages are OpenCV all the way down; `cv2.imread` gives BGR uint8. Every yielded `StageArtifact.image` is BGR. The `greyscale` stage yields a 2-D single-channel array; the `binarized` stage yields `float64` in {0.0, 1.0} because the student normalized after `cv2.threshold` — AD-2 says only `image: ndarray`, so all of this is compliant.

**Unit B — `webui/` Process page (student 2):** Renders `st.image(artifact.image)`. Streamlit interprets 3-channel arrays as **RGB** and float arrays as data in [0.0, 1.0]. Result: every colour stage renders blue-shifted in the browser (the "original" photo of the sheet looks alien on the demo), and any uint8-vs-float mismatch renders black or blown-out. Meanwhile `artifacts.py` (student 3) calls `cv2.imwrite`, which expects BGR uint8 — so the *saved* files are correct and the *browser* is wrong, and nobody's unit has a bug in isolation. UX Voice-and-Tone even jokes "Converting BGR to single-channel luminance" as a *don't* — the spine never says who actually does that conversion.

**Every AD obeyed:** AD-2 (it is a frozen dataclass with an ndarray), AD-3 (pure ndarray-in/ndarray-out), AD-7 (engine never displays).

**Sentence that closes it (tighten AD-2):**
> "`StageArtifact.image` is always `uint8`: 3-channel **BGR** (OpenCV-native) or 2-D single-channel greyscale; never float, never RGBA. Each frontend owns conversion to its toolkit's expectation at the render call (the Web UI converts BGR→RGB via `image[..., ::-1]` / `cv2.cvtColor` before `st.image`; `artifacts.py` and `cv2.imshow` consume BGR as-is)."

---

## F-2 (CRITICAL) — Who persists, and when: generator side-effects vs caller-owned persistence

AD-3 makes processing "a generator … yielding StageArtifact". AD-4 routes all writes through `repository.py`. Neither says **who calls the repository, or at what point in the stream** — and `SheetResult`'s delivery channel is unnamed (generator return value? final yield? separate call?).

**Unit A — `sams.py` + `pipeline.py` (student 1):** Decides the generator is pure (no side effects — that reads as the spirit of AD-3's "pure functions"); the caller iterates, collects, then calls `engine.persist(sheet_result)` explicitly. `sams.py` does exactly that. `SheetResult` arrives via `StopIteration.value` (`result = yield from …`).

**Unit B — `webui/` Process page (student 2):** Reads UX EXPERIENCE.md — "results are persisted to the Local DB automatically on processing", "Saved-to-DB is implicit" — and concludes the *engine* persists as a side effect when the stream completes. The page iterates the generator to feed the stage strip and never calls any persist API. Result: Web-processed sheets are **never written to the DB**; Lookup shows "no data" for sheets Nadeesha just processed; FR-15 parity ("identical Attendance Records") fails silently. Inverse pairing: both decide to persist → double upsert, and the second pass (with `overwrite` defaulting differently per frontend) can clobber a `resolved_by_operator` row that the first pass preserved.

Sub-hazard, same hole: **partial iteration**. A Streamlit rerun or a mid-stream exception abandons the generator at stage 4. If persistence (or artifact saving) is tail-of-stream, an abandoned run half-completes; if it's incremental, an abandoned run half-writes. The spine's one-shot fence (Inherited Invariants) fences *starting* a run, not *abandoning* one.

**Sentence that closes it (new AD, "Pipeline run protocol"):**
> "The pipeline runner owns all side effects: as each stage yields it also writes that stage's image via `artifacts.py`, and after the final stage it persists all Attendance Records via `repository.py` in one transaction, then returns `SheetResult` as the generator's return value (`StopIteration.value`); frontends only iterate and render — they never call `artifacts.py` or any repository write for attendance except the FR-13 resolve API — and a generator abandoned before completion must have written no attendance rows (persistence is atomic at end-of-stream)."

---

## F-3 (MAJOR) — Similarity score direction: is 1.0 a match or a stranger?

AD-2 pins `ReferenceScore(reference_path, score: float 0–1)` — range, but not **direction**. Classic OpenCV signature comparison is naturally a *distance* (ORB descriptor distance, contour `matchShapes` where **0 = identical**, Hausdorff).

**Unit A — `verification.py` (student 1):** Implements `cv2.matchShapes`, normalizes into 0–1, stores it as-is: `score=0.08` means near-identical. `matched = score <= threshold`. `best = min(all_scores)`. All literally compliant — AD-2 constrains range only, and "Similarity metric internals" is explicitly Deferred.

**Unit B — Investigate page + `investigate.py` (students 2, 3):** Render the UX-specified "score on a scale with the threshold marked" assuming right-is-better; the CLI prints "similarity: 0.08 → MATCH", the Web scale draws the marker at 8/100 deep in the red zone next to a green "Match" verdict. `matched: bool` saves the *verdict* from inverting, but the displayed evidence contradicts the verdict on both surfaces — and any frontend that (reasonably) sorts `all_scores` descending to show "best reference first" shows the *worst*. The UX 0–100 normalization assumption also has no assigned owner (engine or frontend?), so CLI prints 0.73 while Web shows 73 — "same score" parity (FR-14) is now a judgement call.

**Sentence that closes it (tighten AD-2):**
> "`ReferenceScore.score` is a **similarity**: monotonically increasing, 1.0 = identical, 0.0 = no similarity; distance-style metrics must be inverted inside `verification.py` before leaving the module; `matched := best.score >= threshold`, `best := max(all_scores, key=score)`; frontends display the raw 0–1 value (the Web scale may label it ×100 but shows the same number to two decimals as the CLI)."

---

## F-4 (MAJOR) — Upsert key: which *form* of Student Index does the DB store?

AD-4 keys attendance on (Student Index, Sheet Identifier). The glossary says both `10009301` and `002` "must resolve everywhere an index is accepted" — which two authors can read as "the repository accepts both".

**Unit A — `mapping.py` (student 1):** Maps row N to the Info File's `no` ordinal — the row-order key it naturally holds — and persists Attendance Records keyed `"001"`. Compliant: AD-2's `StudentRecord` carries both fields; nothing says which one is the key.

**Unit B — `repository.py` + Lookup (student 2):** Implements lookup by normalizing every input to the 8-digit form (the glossary calls the 8-digit Student No "the unique identifier", so that's the honest canonical), then queries `WHERE student_index='10009301'` — zero rows. Every sheet processes "successfully", every lookup says "no data", and both units pass their own unit tests. Worse: the short alias `001` is *per-Info-File* (row ordinal), so two sessions with different rosters can assign `001` to different students — alias-keyed rows silently merge two students' attendance (two owners of one entity, decided by whichever Info File ran last).

**Sentence that closes it (tighten AD-4):**
> "The canonical persisted key is the **8-digit Student No, stored as TEXT**; the short `No` alias is resolved to canonical by one engine helper (`models.py`/`info_file.py`) at every input boundary, and `repository.py` rejects (raises `InputError` on) any key that is not an 8-digit string — aliases never reach a SQL statement."

(Same sentence family should pin `Sheet Identifier` as the ISO-8601 **string** `YYYY-MM-DD`, never a `date` object or datetime — sqlite3 will happily store either and they won't compare equal.)

---

## F-5 (MAJOR) — Concurrent CLI + Web writes: connection lifetime is nobody's problem

The PRD says "single operator", but the *system* runs two processes by design: `streamlit run` stays alive while the marker (UJ-4) or a teammate runs `python sams.py …` against the same `sams.db`. Nothing in AD-4 speaks to connection lifetime, threading, or busy handling.

**Unit A — `repository.py` (student 1):** Opens one module-level `sqlite3.connect()` at import and keeps it forever (simplest compliant reading of "single DB gateway").

**Unit B — `webui/` (student 2):** Caches the repository object with `@st.cache_resource` so pages share it. Two independent failures now ship: (a) Streamlit executes script runs on worker threads, so the cached connection trips sqlite3's default `check_same_thread=True` — `ProgrammingError` on the second page visit; (b) with the Web app holding a write transaction open, the graded CLI hits `sqlite3.OperationalError: database is locked` — a raw stack trace in front of the marker, the exact artifact AD-6 exists to prevent, caused by two units that each obeyed it.

**Sentence that closes it (tighten AD-4):**
> "`repository.py` opens a **short-lived connection per operation** (context-managed unit of work; no connection outlives one engine call), sets `PRAGMA journal_mode=WAL` and `busy_timeout=5000` on every open, and never shares a connection across threads — frontends hold repository *objects*, never live connections."

---

## F-6 (MAJOR) — Reference Signatures: two ADs, no owner for populating `references/`

AD-10 says references live at `references/<student_index>/`; FR-9 says they're crops from sheets 1–3 and "registered into the Local DB on first use". Crops, however, are saved by `artifacts.py` to `output/<Sheet Identifier>/crops/<student_index>.png`. **No unit is assigned the crop→reference promotion, and "first use" has two readings.**

**Unit A — `verification.py` (student 1):** Treats `references/` as operator-provided input (FR-9: "added by dropping files"), registers whatever is there on first `investigate` call, and raises/returns empty when the folder is missing. Compliant with AD-10 to the letter.

**Unit B — `pipeline.py`/`artifacts.py` (student 2):** Saves crops to `output/…/crops/` per AD-10 and stops — AD-10 explicitly gives crops a *different* home than references, so promoting them would trespass on `references/`. Result: on the grader's fresh machine, `python investigate.py 001` runs against an **empty reference set** — either an error (bad) or a vacuous "mismatch" (worse) — unless someone hand-copies crops, a step written down nowhere. Bonus ambiguity inside `crops/<student_index>.png`: which index form (see F-4), and the path allows exactly one probe per student per sheet — fine — but *which sheet's* crop is "the probe" when several exist is also unowned (Investigate page picks latest-by-date? `verification.py` compares all sheets 4–5? SM-4 needs the latter).

**Sentence that closes it (tighten AD-10):**
> "`references/` ships **pre-populated in the submission ZIP** (built once from sheets 1–3 crops by a checked-in `scripts/build_references.py`, run by the team, never by the grader); `verification.py` selects probes as *all* crops for that Student Index from sheets not represented in `references/` (registered crop metadata via `repository.py`), and crop files are named `crops/<8-digit index>.png`."

---

## F-7 (MODERATE) — "per-cell inspection" stage: one artifact or N?

AD-3's registry ends in "per-cell inspection". A sheet has ~40 cells.

**Unit A — `pipeline.py`:** Yields one `StageArtifact(order=7, slug="per-cell-inspection", …)` **per cell** — 40 artifacts, same slug, honestly "yielding StageArtifact from the registry".

**Unit B — `artifacts.py` + `webui/`:** `artifacts.py` writes `NN-slug.png` → 40 successive overwrites, only the last cell survives for the report (SM-3 screenshot damage); the Web stage strip and its "Stage 5 of 7" alt-text pattern assume exactly 7 artifacts and render a 40-row strip; the CLI opens 40 titled windows.

**Sentence that closes it (tighten AD-3):**
> "The registry yields **exactly one StageArtifact per registered stage** per run — 7 artifacts, total, in order, `order` strictly increasing and unique; per-cell inspection emits a single composite image (the deskewed sheet annotated with every cell's ROI and classification)."

---

## F-8 (MODERATE) — Ambiguous resolution: no named write API, so the flag is optional

AD-4 invents `resolved_by_operator` and the survive-reprocessing rule, but names read APIs only (`list_students`, `has_operator_resolutions`). The write path for FR-13 is unnamed.

**Unit A — `repository.py`:** Exposes the generic attendance `upsert(record)` used by the pipeline; sets `resolved_by_operator=0` on upserted rows (they came from detection).

**Unit B — Process page resolve buttons:** Implements one-tap resolution by calling that same upsert with the new status — the only write API that exists. The row flips to Present, `resolved_by_operator` stays 0, and the next re-process silently reverts Nadeesha's hand-fix — precisely the "silent loss of hand resolutions" AD-4 says it prevents. Undo has the same problem in reverse (does restoring Ambiguous clear the flag? Nobody owns the answer).

**Sentence that closes it (tighten AD-4):**
> "`repository.py` exposes exactly two attendance write APIs: `upsert_attendance(records, sheet_id, overwrite: bool)` (pipeline only; skips rows where `resolved_by_operator=1` unless `overwrite`) and `resolve(student_index, sheet_id, status)` (frontends only; sets `resolved_by_operator=1`, or clears it when status is set back to AMBIGUOUS by Undo); frontends never call `upsert_attendance`."

---

## F-9 (MINOR) — `list_students()` source of truth: who inserts students?

Lookup's "no data + valid indices" reads from `repository.list_students()`. But Student Records arrive per-run from the Info File, and no AD says the pipeline persists *students* (AD-4's upsert clause covers attendance only). Pair: `mapping.py` writes attendance rows only (students live in the Info File, per its author) vs Lookup page trusting `list_students()` → the friendly no-data list is permanently empty, and AD-6's specified behavior can't be built. **Fix (tighten AD-4):** "Persisting a sheet upserts its Student Records (canonical index, alias, name, title) into a `students` table; `list_students()` reads only that table."

## F-10 (MINOR) — Web upload has no filename-stem fallback, and no defined failure when the chain exhausts

AD-11's chain ends at "image filename stem". Phone uploads arrive as `IMG_4231.jpg` via `st.file_uploader`; the stem never parses. Pair: `info_file.py` author raises `ProcessingError` when the chain exhausts vs the Process page author who shows the date field "only when the Info File lacks a date" *after* upload — but the page learns the chain exhausted only by calling resolution, which raises mid-flow instead of returning a "needs operator date" signal. **Fix (tighten AD-11):** "Resolution is a total function returning `SheetIdentifierResolution(identifier | needs_operator_date)` — it never raises for an unparseable filename stem; frontends render the date input on `needs_operator_date`, and stems are attempted only for CLI paths (Web uploads skip the stem step)."

---

## Fix list (in priority order)

| # | Severity | AD to touch | One-line fix |
|---|---|---|---|
| F-1 | CRITICAL | AD-2 | Pin `StageArtifact.image` = uint8 BGR/greyscale; frontends convert at render |
| F-2 | CRITICAL | new AD | Runner owns artifact-saving + atomic end-of-stream persistence; `SheetResult` = generator return; frontends only iterate |
| F-3 | MAJOR | AD-2 | `score` is similarity (higher = more similar); `matched := score ≥ threshold`; `best := max` |
| F-4 | MAJOR | AD-4 | Canonical DB key = 8-digit index TEXT (+ ISO string sheet key); aliases resolved before repository |
| F-5 | MAJOR | AD-4 | Per-operation connections, WAL + busy_timeout, no cross-thread sharing |
| F-6 | MAJOR | AD-10 | `references/` pre-built by a team script and shipped; probe set = all non-reference-sheet crops |
| F-7 | MODERATE | AD-3 | Exactly one artifact per registered stage; per-cell inspection = one composite |
| F-8 | MODERATE | AD-4 | Named `resolve()` write API sets/clears `resolved_by_operator`; pipeline and frontends use disjoint write APIs |
| F-9 | MINOR | AD-4 | Sheet persistence upserts Student Records; `list_students()` reads that table |
| F-10 | MINOR | AD-11 | Resolution is total (returns needs-date signal, never raises on stem miss); Web skips stem |
