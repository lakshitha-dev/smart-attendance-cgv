import os

# Suppress OpenCV GUI windows for the whole suite: CLI tests drive sams.main
# end-to-end, and stage windows must neither strobe on desktops nor crash
# headless CI runners (cli_display.py honors this seam).
os.environ.setdefault("SAMS_HEADLESS", "1")

if os.environ["SAMS_HEADLESS"] == "1":
    # Must run before any `matplotlib.pyplot` import in the process (conftest
    # loads before test modules): Agg never opens a window, so infovis tests
    # driving cli_display.show_figure() neither block nor crash headless CI.
    import matplotlib

    matplotlib.use("Agg")
