---
title: SAMS — Experience
project: CGV Group Assignment (CS402.3)
status: final
created: 2026-07-10
updated: 2026-07-10
sources:
  - ../../prds/prd-CGV Group Assignment-2026-07-10/prd.md
  - ../../../../CS402.3 Coursework.md
  - .memlog.md
design: ./DESIGN.md
---

# SAMS — Experience Spine

> Experience spine for the SAMS Web UI (and the graded CLI's display contract). Paired with `DESIGN.md` (Quiet Clerk visual identity). Both spines win over any mockup or working file on conflict. Glossary terms from the PRD (§3) are used verbatim throughout.

## Foundation

Mobile-first responsive web app with desktop as an equal, fully specified surface. The phone is the capture-and-process device — Nadeesha uploads from where the Signing Sheet photo already lives, standing in the corridor. The desktop is the office surface — reviewing results at a desk, taking report screenshots, and driving projector demos. Same three pages, same capabilities, on both (see Responsive & Platform). UI system: **Streamlit multipage app** using native widgets, native sidebar navigation, and `config.toml` theming; custom CSS is minimal. `DESIGN.md` is the visual identity reference; this spine is the experience.

The Web UI is a thin frontend over the **Core Engine** — the same engine the graded **CLI** (`sams.py`, `infovis.py`, `investigate.py`) wraps (FR-15). The Web UI never re-implements detection, persistence, visualization, or verification: stage images come from the engine's emission contract (FR-16), the Lookup chart is the same engine figure the CLI shows, and the Investigate verdict shows the same score and threshold outcome. Runs locally (`localhost`/LAN), single operator, no accounts. Light mode only; English only.

**Delivery conditionality.** The Web UI is gated behind the PRD §6.3 sequencing gate: it is built only once the engine's accuracy metrics (SM-1..SM-3) pass on all five sample sheets. The fallback deliverable is engine + CLI only, and Web UI polish must never consume engine-hardening time (SM-C2). Everything this spine specifies for the Web UI activates only once that gate passes; the CLI Display Contract applies regardless. Streamlit as the UI system was confirmed by the team during UX design (resolving PRD OQ-3 for UX purposes).

## Information Architecture

Three pages on Streamlit's native multipage sidebar. **Process is the landing page** — it is Nadeesha's primary job.

| Page | Page title | Reached from | What lives here |
|---|---|---|---|
| **Process** (landing) | "Mark today's attendance" | App open | Signing Sheet photo upload + Info File upload; Sheet Identifier confirmation (with a date field only when the Info File lacks one); the Process button; live Processing Pipeline stage strip; per-student results list with Present / Absent / Ambiguous statuses; one-tap Ambiguous resolution with Undo; overwrite warning when re-processing a Sheet Identifier that has saved operator resolutions |
| **Lookup** | "Look up a student" | Sidebar | Student Index input (both forms: `10009301` or `002`); attendance summary graph — per-Session Present/Absent timeline with Ambiguous on its own mid-band, and the overall attendance-rate percentage (the engine's FR-8 figure); "no data" response with the list of valid indices |
| **Investigate** | "Check a signature" | Sidebar | Student Index input (both forms); side-by-side Reference Signature vs probe signature images; numeric similarity score on a scale with the threshold marked; plain Match / Mismatch verdict |

Sidebar is Streamlit's default multipage nav, not restyled beyond theme colours. No modals except the overwrite warning; no nested navigation.

→ Visual reference — phone: `mockups/key-process.html` (Process), `mockups/key-lookup.html` (Lookup), `mockups/key-investigate.html` (Investigate); desktop: `mockups/key-process-desktop.html`, `mockups/key-lookup-desktop.html`, `mockups/key-investigate-desktop.html`. Same content and states on both surfaces; layout differs per Responsive & Platform.

→ Composition reference: `.working/directions-1.html` (Direction 1 — Quiet Clerk) — an exploration artifact kept for provenance; the `mockups/` files are the current references. Spine wins on conflict.

## Voice and Tone

Microcopy register: calm, plain-language, no jargon. SAMS talks to Nadeesha like a helpful colleague, not like a pipeline. Full sentences, sentence case, no exclamation marks, no emoji (status glyphs ✓ ✕ ? are semantics, not decoration).

| Moment | Do | Don't |
|---|---|---|
| Upload hint | "Add the sheet photo and the info file, then tap Process. That's all you need to do." | "Select input artifacts to initialize the pipeline" |
| While running | "Reading your photo… (Deskewed)" | "Executing binarization threshold pass 2" |
| Greyscale stage caption | "Any pen colour works — the greyscale step evens it out." | "Converting BGR to single-channel luminance" |
| Pipeline done | "All finished — your results are below." | "Pipeline completed successfully ✓" |
| Results summary | "42 students checked. One needs a quick look from you." | "1 AMBIGUOUS RECORD DETECTED" |
| Ambiguous row | "We couldn't read this signature clearly. Which is right?" | "Confidence below threshold" |
| After resolve | "Saved as Present. Undo" | "Record updated successfully!" |
| Bad image | "We couldn't read that file as a photo. Please add a JPEG or PNG of the Signing Sheet." | "cv2.imread returned None" |
| Bad Info File | "This info file doesn't look right — we couldn't find the student list in it. Check it's the info.xml for this class." | "XML validation error at line 12" |
| Row-count mismatch | "The sheet has 43 signature rows but the info file lists 42 students. Results are matched by row order — please double-check them." | "Row/record cardinality mismatch" |
| Unknown Student Index | "We don't have any attendance saved for that number. Students we do know: 001 (10000409), 002 (10009301)…" | "ERROR: index not found" |
| Empty Lookup / Investigate | "Type a student's number to see their attendance." / "Type a student's number to check their signature." | "No query submitted" |
| Encouragement (all resolved) | "All done. Every student on this sheet is marked." | Confetti, streaks, gamification |

## Component Patterns

Behavioral. Visual specs live in `DESIGN.md` Components.

| Component | Use | Behavioral rules |
|---|---|---|
| File slots (uploader) | Process | Two labelled `st.file_uploader` slots: "Signing Sheet" (JPEG/PNG — both `.png` and `.jpeg`/`.jpg` accepted) and "Info File" (`info.xml`). Each shows filename + "✓ Ready" when accepted. Validation feedback appears at the slot, before Process is tapped where possible. If the Info File lacks a session date, a date field appears to supply the Sheet Identifier (final fallback: image filename stem). |
| Process button | Process | **Explicit one-shot action** (FR-12): processing and Local DB writes happen once per press — never as a side-effect of Streamlit reruns or unrelated widget interaction. Implementation contract: the run is fenced in session state so scrolling, expanding a stage image, or resolving a row never re-triggers the pipeline. Disabled until both inputs are ready. |
| Overwrite warning | Process | If the Sheet Identifier already has saved operator resolutions, tapping Process first asks: "You've already fixed some answers for this sheet by hand." Choice: **Keep resolutions** (the emphasized, primary choice — the safe default, mirroring the CLI's keep-by-default) / **Overwrite everything** (neutral-outlined). Nothing is processed until she chooses. |
| Pipeline stage strip | Process | **Streaming**: each labelled stage image appears as the Core Engine emits it (FR-16), in pipeline order — original → greyscale → denoised → binarized → deskewed → detected table grid → per-cell inspection — with the current stage named while it runs. Completed stages collapse into labelled expanders so the page stays scannable. Images are the engine's emitted artifacts, never a second rendering path. |
| Results row list | Process | One row per Student Record: name, Student Index, status chip ({colors.status-present} / {colors.status-absent} / {colors.status-ambiguous}, always icon + text label). Rendered as a custom row list (containers), not a raw dataframe, so Ambiguous rows can host buttons. Results are persisted to the Local DB automatically on processing; rows reflect saved state. |
| Ambiguous row resolve | Process | The row is visually distinct ({components.result-row-ambiguous}) and offers two buttons: "✓ Present" / "✕ Absent". **One tap updates the Attendance Record instantly** — no confirm dialog — followed by a brief inline Undo affordance ("Saved as Present. Undo"). Undo restores Ambiguous. [ASSUMPTION: Undo remains visible ~5 seconds or until the next interaction; exact duration is a build-time constant] |
| Lookup form | Lookup | Single text input, labelled "Student number". Accepts **both index forms** — the 8-digit Student No (`10009301`) and the short `No` ordinal (`002`); both resolve to the same records (FR-7). Unknown index → the "no data" message listing valid indices — never an error state. |
| Attendance graph | Lookup | The engine's FR-8 Matplotlib figure rendered as-is: per-Session Present/Absent timeline, with Ambiguous as its own mid-band between Present and Absent (distinct ? marks), overall attendance-rate annotated, title + axes + legend. Data-layer parity with `infovis.py` (FR-14). |
| Investigate panel | Investigate | Reference Signature image and probe signature image **side by side** (stacked on narrow phones, grown to a comfortable size on desktop), clearly captioned which is which. Below: the numeric similarity score plotted on a scale with the decision threshold marked, then a plain verdict: "Match — this looks like their usual signature." / "Mismatch — this doesn't look like their usual signature. Worth checking in person." Same score and threshold outcome as `investigate.py` (FR-10, FR-14). When `references/<student_index>/` holds multiple Reference Signatures, the panel shows the probe against the best-matching reference by default, with the remaining references in a collapsed expander. [ASSUMPTION: the score is displayed normalized to a 0–100 scale; the engine's raw metric range is a build-time detail] |

## State Patterns

| State | Page | Treatment |
|---|---|---|
| Empty (first open) | Process | Upload hint + two empty file slots + disabled Process button. No onboarding tour — the page is the instructions (SM-6). |
| Loading (streaming) | Process | The stage strip **is** the loading state: current stage named, completed stage images accumulating in order. No indeterminate spinner as the primary signal. |
| Success | Process | "All finished — your results are below." + results summary line + row list. Saved-to-DB is implicit and stated once: "Results saved." |
| Error | Process | Human-readable message in plain language at the point of failure (slot-level for input errors, page-level for processing errors); never a stack trace (FR-1, FR-12). The page stays usable — inputs are preserved so she can fix and retry. |
| Empty | Lookup / Investigate | Prompt sentence + input. Nothing else. |
| Loading | Lookup / Investigate | Streamlit's native spinner with a plain sentence ("Looking that up…" / "Comparing signatures…"). |
| Success | Lookup / Investigate | Graph / side-by-side panel as specified above. |
| Error | Lookup / Investigate | Only the unknown-index "no data" pattern; engine faults surface as "Something went wrong reading the saved records." |

**Error catalog** (every error is a full sentence telling her what happened and what to do next):

1. **Invalid image** — file can't be decoded as JPEG/PNG at all, or is missing: slot-level message, Process stays disabled. Rejection is decode-level only — a dim, blurry, or skewed photo is valid input that proceeds through normalization and may surface as Ambiguous rows, never as an input error (UJ-1).
2. **Invalid / mismatched Info File** — fails schema validation (Appendix A) or doesn't contain a student list: slot-level message naming the file, not the parser.
3. **Row-count mismatch** — detected student rows ≠ Info File Student Records (FR-3/FR-5): processing completes, results show, but a prominent flag banner sits above the results ("matched by row order — please double-check"). A flag, not a failure.
4. **Unknown Student Index** — Lookup/Investigate: "no data" + the list of valid indices (FR-7). Never an error tone.

## Interaction Primitives

- **Touch targets ≥ 44px** on every interactive element (Process button 52px, resolve buttons 46px, uploader rows ≥ 48px) — on every surface, regardless of pointer.
- **Single column on phone.** No horizontal scrolling for any core flow, on any surface (FR-14 NFR). Anything wide (stage images) scales to its column width; tap to view larger via the native fullscreen affordance. Desktop layouts widen per Responsive & Platform below — never by scrolling sideways.
- **Explicit action semantics.** Nothing processes, writes, or overwrites without a deliberate tap: Process is one-shot (FR-12), resolution is per-row, overwrite requires a choice. The only "instant" action is Ambiguous resolution — and it carries Undo.
- **Tap is the whole vocabulary.** No long-press, no swipe gestures, no drag. Desktop gets the same vocabulary with pointer + keyboard — every action works identically with a click.
- **Banned:** carousels, auto-playing anything, toasts that carry information available nowhere else, confirm dialogs for reversible actions, multi-step wizards.

## Responsive & Platform

One responsive app, two first-class surfaces. Streamlit's native behavior carries most of it: the sidebar collapses to a hamburger on narrow viewports and stays visible on wide ones, and `st.columns` gives side-by-side layout on desktop. Use only column layouts that degrade gracefully to a stack.

- **Breakpoints.** Phone (below ~768px): single column, sidebar collapsed to the hamburger. Desktop (~768px and up): sidebar visible, content column max-width ~1100px, centered.
- **Process on desktop** — two columns: left carries the upload slots and the pipeline stage strip (stages as a vertical labelled list with larger thumbnails); right carries the results summary and the results row list. The overwrite warning presents as a centered, modal-style choice.
- **Lookup on desktop** — input row on top; the attendance graph takes the full content width (the Matplotlib figure earns the room). The "no data" valid-indices list flows in two columns.
- **Investigate on desktop** — the side-by-side signatures grow to a comfortable size, the score scale runs full width beneath them, and the Match / Mismatch verdict stays prominent. The "Other reference signatures" expander shows a thumbnail row.
- **Degradation rule.** Every desktop column pair stacks back to the phone order already specified in Component Patterns and Key Flows. No content exists on one surface only — parity of capability across surfaces.
- **Pointer vs touch.** Hover states are allowed on desktop (a subtle row hover tint, `{colors.row-hover}` in `DESIGN.md`) but hover is never required to reveal information. Touch targets stay ≥ 44px everywhere regardless of pointer.
- **Demo / projector.** The desktop layout doubles as the viva demo view: pipeline thumbnails and status chips must read from 2–3 m away — no critical information below a 14px equivalent.

## Accessibility Floor

Behavioral. Visual contrast lives in `DESIGN.md`.

- **Statuses are never colour-only**: every status renders icon + text label (✓ Present, ✕ Absent, ? Ambiguous) alongside its colour, in rows, in the summary counts, and in chart legends. The whole UI must survive greyscale.
- **Labels on all inputs**: both file slots, the Student Index inputs, and the date field carry visible text labels (not placeholder-only).
- **Keyboard operable on desktop**: every action — upload, Process, resolve, Undo, lookup, investigate — reachable and firable via Tab/Enter in reading order (Streamlit natives provide this; custom rows must use real buttons, not click-handlers on divs).
- **Alt text on every stage image** ("Stage 5 of 7 — Deskewed sheet") and on both Investigate signature images ("Reference Signature for 10009301", "Signature from sheet 2019-05-31").
- Status changes (resolve, Undo, processing complete) are announced as text on the page, not only by colour or motion.

## CLI Display Contract

The graded CLI's stage display is UX-owned behavior (FR-11 / FR-16), even though the CLI has no visual identity layer.

- **Single display contract:** the Core Engine exposes pipeline progress as a sequence of labelled stage images via callback/generator and **never opens display windows itself** (`cv2.imshow` is forbidden inside the engine). One emission path serves both frontends; stage names and order are identical in CLI and Web UI output (FR-16). The engine is importable and testable headlessly.
- **CLI rendering (`sams.py`):** each major stage is displayed live in an OpenCV window **while processing, in pipeline order** — original, greyscale, denoised, binarized, deskewed, detected table grid, per-cell inspection — each window titled with its stage name (saving alone does not satisfy FR-11). [ASSUMPTION: stage windows display non-blocking as processing continues; a final keypress dismisses the display — blocking-per-stage vs non-blocking is a build-time choice the brief doesn't fix]
- **Saved copies:** every stage is additionally saved as a labelled image file, named in pipeline order, into a per-sheet folder under the project root — `output/<Sheet Identifier>/NN-stage.png` (e.g. `output/2019-05-31/05-deskewed.png`) — so processing all five sample sheets never overwrites earlier report screenshots. These are the report's "screenshots of the entire step-by-step process".
- **Stage vocabulary is shared verbatim** between CLI window titles, saved filenames, Web UI stage strip labels, and alt text.
- **Textual results output:** after processing, `sams.py` prints a per-student attendance summary to stdout — Student Index, name, and Present / Absent / Ambiguous — so a grader sees who was present without opening the Local DB.
- **Error experience:** failures produce a clear one-line human-readable error and a non-zero exit code — never a raw stack trace. On a successful load, the CLI reports the record count and the Sheet Identifier it resolved.
- **Sheet Identifier fallback:** when the Info File lacks a date, the CLI accepts the Sheet Identifier via a flag (mirroring the Web UI's date field); the final fallback is the image filename stem.
- **Re-processing:** re-running `sams.py` on a Sheet Identifier keeps saved operator resolutions by default; replacing them requires an explicit `--overwrite` flag (the CLI mirror of the Web UI's overwrite warning).
- **Ambiguous is first-class in the CLI:** Ambiguous is a persisted status, not a Web-UI nicety — `sams.py` prints it in the summary, `infovis.py`'s graph shows it distinct (FR-8), and resolving it to Present or Absent is available only in the Web UI (or by re-processing). The CLI never silently coerces Ambiguous to Absent.

## Key Flows

Inherited verbatim from PRD §2.3 (UJ-1..UJ-4); Nadeesha is the named protagonist for UJ-1–UJ-3.

### Flow 1 — UJ-1. Nadeesha records a session's attendance from her phone.

1. Nadeesha has just photographed the signed sheet for the 31/05 CGV lecture on her phone. She opens the SAMS Web UI in her phone browser — it lands on Process.
2. She adds the photo to the Signing Sheet slot and `info.xml` to the Info File slot; both show "✓ Ready".
3. She taps **Process** (if this Sheet Identifier already had hand-fixed answers, she'd first choose Keep resolutions / Overwrite everything).
4. The stage strip streams: original → greyscale → denoised → binarized → deskewed → detected table grid → per-cell inspection, each labelled image appearing as it completes.
5. "All finished — your results are below." The per-student list shows ✓ Present and ✕ Absent chips; results are saved to the Local DB automatically.
6. One row is ? Ambiguous — the badly-scrawled signature. The row raises its hand: "We couldn't read this signature clearly. Which is right?"
7. **Climax:** she glances at the sheet in her other hand, taps "✓ Present" — the row flips instantly to ✓ Present with "Saved as Present. Undo". Done, on her phone, standing in the corridor.
8. She repeats for the other sheets.

Failure: a file that can't be decoded as JPEG/PNG at all → slot-level plain-language error; inputs preserved, she re-shoots and retries. A dim-but-readable photo is **not** an input error — it flows through the pipeline (normalization does its work) and may simply surface more ? Ambiguous rows for her to resolve (UJ-1).

### Flow 2 — UJ-2. Nadeesha reviews one student's attendance.

1. A lecturer asks about student `10009301`.
2. She opens **Lookup** from the sidebar and types the number — either form works (`10009301` or `002`).
3. **Climax:** the attendance graph appears — per-Session Present/Absent timeline with the overall attendance rate — and she reads the answer straight to the lecturer, off her phone in the corridor or her desktop at the office.

Failure: unknown number → "We don't have any attendance saved for that number" + the list of students SAMS does know.

### Flow 3 — UJ-3. Nadeesha verifies a suspicious signature.

1. Suspecting a proxy signer for `10009301`, she opens **Investigate** from the sidebar and enters the index.
2. The Reference Signature and the signature captured from the probe sheet appear side by side, clearly captioned.
3. **Climax:** below them, the similarity score sits on a scale with the threshold marked, and the plain verdict settles it: "Mismatch — this doesn't look like their usual signature. Worth checking in person." She has evidence, not just a hunch.

### Flow 4 — UJ-4. The marker runs the brief's exact commands.

1. Dr. Ranaweera (or a grader) unzips the submission on a fresh machine and installs dependencies in one step (`pip install -r requirements.txt`; no web dependencies needed for the CLI).
2. `python sams.py 10.07.2019.png info.xml` — OpenCV windows show each labelled pipeline stage live, in order, per the CLI Display Contract; labelled stage images land in the output folder; Attendance Records land in the Local DB.
3. `python infovis.py 001` — the same Matplotlib attendance figure the Web UI shows.
4. `python investigate.py 001` — the same similarity score and Match/Mismatch verdict.
5. **Climax:** every command produces the same detections, graphs, and verdicts as the Web UI, from the same Core Engine and Local DB — the parity is visible, and the step-by-step display gives the report its screenshots.
