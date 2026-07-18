import os

import pytest

# Suppress OpenCV GUI windows for the whole suite: CLI tests drive sams.main
# end-to-end, and stage windows must neither strobe on desktops nor crash
# headless CI runners (cli_display.py honors this seam).
os.environ.setdefault("SAMS_HEADLESS", "1")

if os.environ["SAMS_HEADLESS"].lower() not in ("0", "", "false", "no"):
    # Any truthy value counts ("1", "true", "yes") — an exact-"1" check would
    # silently keep the GUI backend for SAMS_HEADLESS=true. Must run before
    # any `matplotlib.pyplot` import in the process (conftest loads before
    # test modules): Agg never opens a window, so figure-producing tests
    # neither block nor crash headless CI.
    import matplotlib

    matplotlib.use("Agg")


@pytest.fixture(autouse=True)
def _close_matplotlib_figures():
    """Figures register in pyplot's global manager; leaking one per test
    trips matplotlib's 20-figure warning and grows memory across the suite."""
    yield
    import sys

    plt = sys.modules.get("matplotlib.pyplot")
    if plt is not None:
        plt.close("all")
