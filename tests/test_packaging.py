"""Story 1.7 packaging guards (FR-15, AD-1/AD-8): the fresh-machine promises,
pinned as tests so they cannot silently regress.

- The grader path (engine + all three CLI entry scripts) must be importable
  with ZERO web dependencies — streamlit lives only under webui/.
- Entry scripts stay thin (<50 lines, AD-1 — the architecture's budget is
  literal file lines).
- requirements.txt is the ONE-STEP install: exact pins, engine/CLI deps only;
  requirements-web.txt extends it; requirements-dev.txt must never smuggle a
  web package into the "web-free" test venv the fresh-machine proof relies on.
- Nothing in the engine/CLI (or webui) source hardcodes an absolute path — a
  fresh unzip runs from any directory (FR-15).
- The deliverables the marker depends on exist and are git-tracked (a
  .gitignore rule once shadowed README.md).
"""

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY_SCRIPTS = ("sams.py", "infovis.py", "investigate.py")
GRADER_PATH_SOURCES = [ROOT / name for name in ENTRY_SCRIPTS] + [
    ROOT / "cli_display.py",
    *sorted((ROOT / "sams_core").rglob("*.py")),
]
WEB_MODULE_PREFIXES = ("streamlit", "tornado", "pydeck", "altair", "webui")


def _pins(path: Path) -> dict[str, str]:
    """Parse a requirements file into {normalized-name: version}, strictly.

    utf-8-sig tolerates a PowerShell BOM; names are PEP 503-normalized;
    inline comments are stripped; duplicate names and non-numeric versions
    fail loudly (a conflicting or nonsense pin must never certify)."""
    pins: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.split(" #")[0].split("\t#")[0].strip()
        if not line or line.startswith(("#", "-r ")):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==(\d[A-Za-z0-9.+]*)", line)
        assert match, f"{path.name}: not an exact pin: {raw!r}"
        name = re.sub(r"[-_.]+", "-", match.group(1)).lower()
        assert name not in pins, f"{path.name}: duplicate pin for {name}"
        pins[name] = match.group(2)
    return pins


def _directives(path: Path) -> list[str]:
    """Non-comment `-r`/`-c` directive lines (comments must not count)."""
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip().startswith(("-r ", "-c "))
    ]


def test_engine_and_cli_import_graph_is_web_free():
    """Import the three entry scripts AND every sams_core submodule (lazy
    imports included) in one scrubbed fresh interpreter, then assert no web
    framework — nor webui itself — ever entered sys.modules (AD-8)."""
    probe = (
        "import pkgutil, importlib, sys; "
        "import sams, infovis, investigate, cli_display; "
        "import sams_core; "
        "[importlib.import_module('sams_core.' + m.name) "
        " for m in pkgutil.iter_modules(sams_core.__path__)]; "
        f"bad = [m for m in sys.modules if m.startswith({WEB_MODULE_PREFIXES!r})]; "
        "assert not bad, f'web modules reachable from CLI path: {bad}'"
    )
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("PYTHONPATH", "PYTHONSAFEPATH", "PYTHONSTARTUP")
    }
    env["SAMS_HEADLESS"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=120,
        env=env,
    )
    assert result.returncode == 0, result.stderr


def test_no_web_import_statement_in_grader_path_sources():
    """Prose may MENTION Streamlit (docstrings explain thread-safety design);
    import statements — including comma-form `import os, streamlit` and any
    engine->webui layering violation — are what AD-8 forbids."""
    import_pattern = re.compile(
        r"^\s*(?:from\s+(?:streamlit|webui)\b"
        r"|import\s+(?:[\w.]+\s*,\s*)*(?:streamlit|webui)\b)",
        re.MULTILINE,
    )
    for source in GRADER_PATH_SOURCES:
        assert not import_pattern.search(source.read_text(encoding="utf-8")), (
            f"{source.name} imports a web module — web code belongs under webui/ only (AD-8)"
        )


def test_entry_scripts_stay_thin():
    for name in ENTRY_SCRIPTS:
        line_count = len((ROOT / name).read_text(encoding="utf-8").splitlines())
        assert line_count < 50, f"{name} is {line_count} lines — AD-1 requires <50"


def test_requirements_txt_is_pinned_and_web_free():
    pins = _pins(ROOT / "requirements.txt")
    assert not _directives(ROOT / "requirements.txt")
    assert set(pins) == {"opencv-python", "numpy", "matplotlib"}, (
        f"requirements.txt must hold exactly the engine/CLI deps (AD-8), got: {sorted(pins)}"
    )


def test_requirements_web_extends_core_and_pins_streamlit():
    path = ROOT / "requirements-web.txt"
    assert "-r requirements.txt" in _directives(path), (
        "requirements-web.txt must include the core pins via a real (non-comment) -r line"
    )
    assert "streamlit" in _pins(path)


def test_requirements_dev_is_web_free_and_extends_core():
    """The dev file is the one door into the 'web-free' venv the fresh-machine
    proof runs in — a web package here silently voids that evidence."""
    path = ROOT / "requirements-dev.txt"
    assert "-r requirements.txt" in _directives(path)
    pins = _pins(path)
    assert "pytest" in pins
    forbidden = {name for name in pins if name.startswith(WEB_MODULE_PREFIXES)}
    assert not forbidden, f"requirements-dev.txt must stay web-free (AD-8): {forbidden}"


def test_no_absolute_paths_in_sources():
    """FR-15: a fresh unzip runs from any directory. Scans engine, CLI, and
    webui sources for hardcoded roots (drive letters, UNC, common POSIX roots,
    bare "C:" join-style literals)."""
    pattern = re.compile(
        r"[\"'](?:[A-Za-z]:[\\/]"
        r"|\\\\\\\\"
        r"|/(?:home|Users|tmp|var|etc|opt|mnt|srv)/)"
        r"|[\"'][A-Za-z]:[\"']"
    )
    sources = GRADER_PATH_SOURCES + sorted((ROOT / "webui").rglob("*.py"))
    for source in sources:
        for n, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
            assert not pattern.search(line), f"absolute path in {source.name}:{n}: {line.strip()}"


def test_marker_facing_deliverables_exist_and_are_tracked():
    """README.md was once listed in .gitignore — the flagship deliverable must
    be present AND tracked, along with the brief's verbatim-command inputs
    and the committed references investigate.py depends on."""
    for deliverable in ("README.md", "10.07.2019.png", "info.xml", "requirements.txt"):
        assert (ROOT / deliverable).exists(), f"{deliverable} missing from the repo"
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "README.md"],
        capture_output=True,
        cwd=str(ROOT),
        timeout=30,
    )
    ignored = subprocess.run(
        ["git", "check-ignore", "README.md"],
        capture_output=True,
        cwd=str(ROOT),
        timeout=30,
    )
    assert tracked.returncode == 0, "README.md is not git-tracked"
    assert ignored.returncode != 0, "README.md is matched by .gitignore — remove the rule"
    assert (ROOT / "references").is_dir() and any((ROOT / "references").iterdir()), (
        "references/ is a committed input for investigate.py — it must ship in the repo/ZIP"
    )
