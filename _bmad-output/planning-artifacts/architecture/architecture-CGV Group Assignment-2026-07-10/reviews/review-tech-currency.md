# Review — Technology Currency & Reality-Check Lens

- **Artifact:** `ARCHITECTURE-SPINE.md` (architecture-CGV Group Assignment-2026-07-10)
- **Lens:** every committed stack decision must be web-verified against live sources, not asserted from training data
- **Reviewed:** 2026-07-10
- **Verdict:** **pass-with-fixes**

The spine's claim "Versions verified on the web 2026-07-10" holds up almost entirely: every pinned version exists, is the current release, and the pin set co-resolves. Four fixable inaccuracies remain, one of which (the "3.10+ works" claim) is factually contradicted by the spine's own numpy pin.

---

## What was verified (live sources, 2026-07-10)

| Spine claim | Live reality | Status |
| --- | --- | --- |
| opencv-python 5.0.0.93 | Latest on PyPI, uploaded 2026-07-02. Wheels: win32/win_amd64/manylinux x86_64+aarch64/macOS arm64+x86_64, all cp37-abi3. | CONFIRMED |
| OpenCV 5 Python API compatible for classical CV | Official 4→5 migration guide: Python cv2 API backward-compatible for classical CV; imread/cvtColor/threshold/findContours unchanged. G-API and classic ML moved to opencv_contrib; Features2D renamed Features but SIFT/ORB/FAST/MSER stay in main. None of the moved modules are used by SAMS. | CONFIRMED |
| numpy 2.5.1 | Latest on PyPI (2026-07-04; 2.5.0 was 2026-06-21). | CONFIRMED |
| opencv-python × numpy 2 binary compatibility | opencv-python 5.0.0.93 metadata declares `numpy>=2; python_version >= "3.9"` with **no upper bound**; wheels built against the NumPy 2 ABI. `opencv-python==5.0.0.93` + `numpy==2.5.1` co-resolve and are runtime-compatible. | CONFIRMED |
| streamlit 1.59.1 | Latest on PyPI, released 2026-07-08 (two days before spine date). `st.file_uploader`, `st.Page`/`st.navigation` multipage, and `config.toml` `[theme]` (incl. `[theme.light]`/`[theme.dark]` tables) all current and non-deprecated in 2026 docs. | CONFIRMED |
| matplotlib 3.11.x | 3.11.0 is the latest (released 2026-06-12); no 3.11.1 exists yet. Wheels cp310–cp314. | CONFIRMED (exact patch is .0 — see F3) |
| sqlite3, xml as stdlib | Both remain in the CPython 3.12/3.13 stdlib; no deprecation affecting them. | CONFIRMED |
| Python 3.12 target | Sensible: all four pins ship 3.12 wheels; opencv-python wheels are abi3 so 3.13 also works. There is a known opencv-python wheel-gap complaint for 3.14 (opencv-python#1155), so 3.12 is the safe choice. | CONFIRMED (but see F1) |

## Findings

### F1 — MEDIUM — "(3.10+ works)" is false under the spine's own pins

Spine Stack table: `Python | 3.12 target (3.10+ works)`. **numpy 2.5.1 declares `requires_python: >=3.12`** and ships wheels only for cp312/cp313/cp314. matplotlib 3.11.0 also does not support anything the numpy pin allows below 3.12. With the pinned requirements.txt, Python 3.10 and 3.11 fail at install time. This matters for the graded fresh-machine install path (FR-15): a grader or teammate on 3.10/3.11 gets a resolver error.
**Fix:** change to "3.12 target (3.12+ required by pinned numpy 2.5.1)" — or relax the numpy pin (e.g. numpy 2.2.x supports 3.10–3.13) if broad interpreter tolerance is actually wanted.

### F2 — MEDIUM — Fallback pin "4.12.x" is stale; the current 4.x line is 4.13.0.x

The [ASSUMPTION] fallback says "pin 4.12.x instead." The live 4.x line is **4.13.0** (opencv-python-headless 4.13.0.92 confirmed on PyPI; docs.opencv.org serves 4.13.0 as the current 4.x docs). 4.12.x is two-plus releases behind within its own line. If the fallback fires, it should land on the maintained 4.x head.
**Fix:** reword fallback to "pin the latest 4.13.0.x wheel (4.13.0.92 as of 2026-07-10)."

### F3 — LOW — opencv-python 5.0.0.93 is 8 days old at spine date; bleeding-edge primary pin for graded coursework

5.0.0.93 (2026-07-02) is the first stable 5.x wheel release — OpenCV's first major since 2018. The classical-CV API used by SAMS is officially backward-compatible, and the spine's [ASSUMPTION] escape hatch is correctly present, so this is not a blocker. But for coursework graded on a fresh machine against course labs almost certainly written for 4.x, the conservative default is inverted: pin 4.13.0.x as primary and note 5.x as the forward option. Also verify any course-provided tutorial code before committing to 5.x (e.g. anything touching cv2.ml or G-API would break — SAMS doesn't, per the spine's module list).
**Fix (optional):** flip primary/fallback, or keep as-is but resolve the [ASSUMPTION] against the actual course lab material before the first story.

### F4 — LOW — "matplotlib 3.11.x" is a range, not a pin; exact current patch is 3.11.0

The Stack table's other rows are exact pins; matplotlib's is "3.11.x". Current exact is **3.11.0** (no 3.11.1 exists). AD-8 says requirements.txt is "pinned," so the spine should state the resolvable value.
**Fix:** write `matplotlib 3.11.0 (latest as of 2026-07-10)`.

### F5 — INFO — Streamlit multipage + config.toml theming: one known live wart

streamlit 1.59.1 is current and everything the spine leans on (file_uploader, st.Page/st.navigation, [theme] tables) works as assumed. One open upstream issue (streamlit#11797): with `[theme]` set in config.toml, deep-linking directly to a sub-page URL of an st.navigation app can bounce to the default page. Localhost-only usage and the spine's Process→Lookup→Investigate flow make this cosmetic, but the webui story owner should know it exists. Also note 1.59.1 shipped 2026-07-08 — two days old; a `~=1.59` spec in requirements-web.txt would be marginally safer than an exact pin for a non-graded extra.

## Verdict rationale

No named technology is dead, wrong, or incompatible; the headline risk the lens targeted — opencv-python wheels vs numpy 2.x ABI — is affirmatively confirmed compatible (declared `numpy>=2`, no cap). The failures are precision errors: a false interpreter-range claim (F1), a stale fallback version (F2), and a range-vs-pin inconsistency (F4). All are one-line edits. Hence **pass-with-fixes**.

## Sources

- https://pypi.org/project/opencv-python/ (5.0.0.93, 2026-07-02; branches; wheel platforms)
- https://pypi.org/pypi/opencv-python/5.0.0.93/json (requires_dist `numpy>=2; python_version>="3.9"`, `numpy<2.0; python_version<"3.9"`; requires_python >=3.6; cp37-abi3 win_amd64 wheel)
- https://github.com/opencv/opencv/wiki/OpenCV-4-to-5-migration and https://opencv.org/opencv-5/ (Python API compatibility; G-API/ML → contrib; Features rename; NumPy 2.x support)
- https://docs.opencv.org/4.13.0/ and https://pypi.org/project/opencv-python-headless/ (4.13.0.92 — current 4.x line)
- https://github.com/opencv/opencv-python/issues/1155 (Python 3.14 wheel gap complaint)
- https://pypi.org/pypi/numpy/2.5.1/json (requires_python >=3.12; cp312–cp314 wheels; 2.5.1 released 2026-07-04)
- https://pypi.org/project/streamlit/ and https://docs.streamlit.io/develop/quick-reference/release-notes/2026 (1.59.1, 2026-07-08)
- https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader, https://docs.streamlit.io/develop/api-reference/configuration/config.toml (features current)
- https://github.com/streamlit/streamlit/issues/11797 (multipage + theme deep-link issue)
- https://pypi.org/project/matplotlib/ (3.11.0, 2026-06-12; no 3.11.1)
