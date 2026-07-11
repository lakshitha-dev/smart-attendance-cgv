# SAMS Project — Sprint Selection

One sprint per person. Reply with your top 2 choices.

Each sprint is one complete feature you build alone, start to finish (code + tests). It becomes your individual contribution chapter in the report (about 2 pages). Every story ID below has a ready-made story file in `_bmad-output/implementation-artifacts/` with full acceptance criteria and dev notes.

---

## Sprint 1 — Foundation & Input Handling

Program entry, read and validate the sheet photo and info.xml, error handling. You set up the project everyone builds on.

- **Stories:** 1.1
- **Difficulty:** ⭐⭐
- **Note:** must be fast — finishes Day 1

## Sprint 2 — Image Preprocessing

Greyscale, denoise, binarize, and deskew with OpenCV, plus the live step-by-step display and saved stage images.

- **Stories:** 1.2
- **Difficulty:** ⭐⭐⭐

## Sprint 3 — Table & Cell Detection

Find the student table in the photo, detect the grid, extract each signature box.

- **Stories:** 1.3
- **Difficulty:** ⭐⭐⭐⭐
- **Note:** hard computer-vision puzzle

## Sprint 4 — Signature Detection

Measure the ink, decide Present / Absent / Unclear per student. The core decision-maker.

- **Stories:** 1.4
- **Difficulty:** ⭐⭐⭐⭐

## Sprint 5 — Database & Accuracy Testing

Save results to SQLite, map detections to students, build the test proving 100% accuracy, lead final integration.

- **Stories:** 1.5, 1.6
- **Difficulty:** ⭐⭐⭐
- **Note:** also acts as team integrator

## Sprint 6 — Attendance Charts

infovis.py end-to-end: student lookup, Matplotlib attendance timeline graph, plus the web Lookup page.

- **Stories:** 2.1, 2.2, 4.5
- **Difficulty:** ⭐⭐⭐

## Sprint 7 — Signature Verification

investigate.py end-to-end: reference signatures, similarity comparison, catch fake signers, evaluation, plus the web Investigate page.

- **Stories:** 3.1, 3.2, 3.3, 4.6
- **Difficulty:** ⭐⭐⭐⭐⭐
- **Note:** hardest sprint, biggest grade upside

## Sprint 8 — Web App & Packaging

The Streamlit app: upload from phone, watch processing live, fix unclear rows with one tap, plus final packaging for the marker's machine.

- **Stories:** 4.1, 4.2, 4.3, 4.4, 4.7, 1.7
- **Difficulty:** ⭐⭐⭐
- **Note:** most stories, but they are thin UI wrappers

---

## How It Works

1. **Day 1** — everyone meets to set up shared contracts and test data
2. **Days 2–7** — everyone builds their own sprint independently
3. **Days 8–9** — we connect everything together
4. **Day 10** — report and submit

Strong OpenCV people should take Sprint 3, 4, or 7.

## Selections

| Sprint | Topic | Stories | Member |
|---|---|---|---|
| 1 | Foundation & Input Handling | 1.1 | |
| 2 | Image Preprocessing | 1.2 | |
| 3 | Table & Cell Detection | 1.3 | |
| 4 | Signature Detection | 1.4 | |
| 5 | Database & Accuracy Testing | 1.5, 1.6 | |
| 6 | Attendance Charts | 2.1, 2.2, 4.5 | |
| 7 | Signature Verification | 3.1, 3.2, 3.3, 4.6 | |
| 8 | Web App & Packaging | 4.1, 4.2, 4.3, 4.4, 4.7, 1.7 | |

Coverage: all 19 project stories are delegated across the 8 sprints — nothing left over.

Full details per sprint (skills, fixtures, independence rules): `topic-selection.md`
