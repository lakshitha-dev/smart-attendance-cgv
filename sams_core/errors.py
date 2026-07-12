class SamsError(Exception):
    """Base for all engine-raised errors. Engine raises; only the CLI prints/exits."""


class InputError(SamsError):
    """Bad image or Info File input — CLI exit code 2."""


class ProcessingError(SamsError):
    """Pipeline failure after inputs were accepted — CLI exit code 1."""
