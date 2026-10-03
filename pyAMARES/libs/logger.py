import sys

from loguru import logger

DEFAULT_LOG_LEVEL = "INFO"

# loguru's built-in handler writes to stderr, which Jupyter renders as red
# output, and its default format prepends a timestamp and module:function:line.
LOG_FORMAT = "[AMARES | {level}] {message}"

# id of the handler this module owns, so repeated calls replace it instead of
# dropping handlers the host application installed.
_handler_id = None


def _skip_batch_info(record):
    # BATCH_INFO belongs in the rotating log file that
    # run_parallel_fitting_with_progress opens, not on the console.
    return record["level"].name != "BATCH_INFO"


def set_log_level(level=DEFAULT_LOG_LEVEL):
    """
    Set the console log level for pyAMARES.

    On import, pyAMARES replaces loguru's default handler, which shows every
    message down to DEBUG, with one that writes ``level`` and above to stdout.
    Only that default handler is removed, so a handler installed by an
    application embedding pyAMARES keeps working.

    Args:
        level (str, optional): The lowest level to show. One of "TRACE", "DEBUG",
          "INFO", "SUCCESS", "WARNING", "ERROR" or "CRITICAL", case-insensitive.
          Defaults to "INFO".

    Examples:
        >>> from pyAMARES.libs.logger import set_log_level
        >>> set_log_level("debug")  # show the per-fit diagnostics
    """
    global _handler_id

    if _handler_id is None:
        try:
            logger.remove(0)  # loguru's default stderr handler
        except ValueError:
            pass  # the application removed it before importing pyAMARES
    else:
        logger.remove(_handler_id)

    _handler_id = logger.add(
        sys.stdout,
        level=level.upper(),
        format=LOG_FORMAT,
        filter=_skip_batch_info,
    )
