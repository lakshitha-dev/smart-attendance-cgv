import os

# Suppress OpenCV GUI windows for the whole suite: CLI tests drive sams.main
# end-to-end, and stage windows must neither strobe on desktops nor crash
# headless CI runners (cli_display.py honors this seam).
os.environ.setdefault("SAMS_HEADLESS", "1")
