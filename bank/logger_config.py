"""Logging setup for the banking system.

The assignment asks for two things:
  1. Messages printed on screen.
  2. Errors and warnings written to a file inside the ``logs`` folder.

We do this with one logger and two *handlers*. A handler decides where a
log message goes and which levels it lets through.
"""

import logging
import os

# Folder and file where warnings/errors are stored.
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "bank.log")


def get_logger(name="bank"):
    """Return a logger that prints to screen and writes warnings to a file.

    Args:
        name (str): Name of the logger. Using one shared name means every
            module gets the same logger and the same handlers.

    Returns:
        logging.Logger: The configured logger.
    """
    logger = logging.getLogger(name)

    # Only add handlers the first time, otherwise each call would add
    # another copy and every message would be printed several times.
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    os.makedirs(LOG_DIR, exist_ok=True)

    # Handler 1: the screen. Shows INFO and above, in a short format.
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    # Handler 2: the log file. Only WARNING and above, with a timestamp.
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(module)s | %(message)s"))

    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger
