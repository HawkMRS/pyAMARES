import logging
import sys

LOG_MODES = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

# GLOBAL VARIABLE: LOG_STYLE
#     The output mode for the log messages. Options:
#     - "plain": Uses `logging.Formatter` and logs to stdout.
#                Always displays plain text messages in all environments.
#     - "stderr": Uses `logging.Formatter` and logs to stderr.
#                 This is the normal behaviour of the python logging module, but
#                 produces red output in Jupyter notebooks.
#
# Accessed by get_logger:
LOG_STYLE = "plain"

# GLOBAL VARIABLE: DEFAULT_LOG_LEVEL
#     The default log level for all loggers. Options:
#     - "debug", "info", "warning", "error", "critical"
#
# Accessed by get_logger and set_log_level:
DEFAULT_LOG_LEVEL = "info"


def get_logger(
    name: str, format_string: str = "[AMARES | {levelname}] {message}"
) -> logging.Logger:
    """
    Get or create a logger with the specified name and format.

    If the logger has no existing handlers, it initializes one based on the provided log style.
    The log level defaults to `DEFAULT_LOG_LEVEL`. To change it globally, use `set_log_level()`.

    Parameters
    ----------
    name : str
        The name of the logger.
    format_string : str, optional
        The format string for log messages (default: "[AMARES | {levelname}] {message}").

    Returns
    -------
    logging.Logger
        A configured logger instance.

    Raises
    ------
    ValueError
        If an invalid `LOG_STYLE` is provided.

    Examples
    --------
    >>> logger = get_logger("example_logger")
    >>> logger.debug("This is a debug message.")
    [DEBUG] example_logger: This is a debug message.
    """
    global LOG_STYLE

    logger = logging.getLogger(name)
    logger.setLevel(LOG_MODES.get(DEFAULT_LOG_LEVEL, logging.ERROR))

    if not logger.hasHandlers():
        if LOG_STYLE == "plain":
            formatter = logging.Formatter(format_string, style="{")
            handler = logging.StreamHandler(sys.stdout)
        elif LOG_STYLE == "stderr":
            formatter = logging.Formatter(format_string, style="{")
            handler = logging.StreamHandler()
        else:
            raise ValueError(
                f"Invalid mode: '{LOG_STYLE}'. Choose from 'plain' or 'stderr'."
            )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def set_log_level(level: str = DEFAULT_LOG_LEVEL, verbose: bool = True):
    """
    Set the global logging level for all loggers.

    This function sets the logging level across the entire application using
    the basicConfig method of the logging module. It also ensures that all
    existing loggers adhere to this global level.

    Parameters
    ----------
    level : str
        The logging level to set globally. Acceptable values are 'critical',
        'error', 'warning', 'info', 'debug', and 'notset'. Default is the
        `DEFAULT_LOG_LEVEL`.

    verbose : bool
        Print an overview of the log levels and highlight the selected level.

    Examples
    --------
    >>> set_log_level('info')
    >>> logger = logging.getLogger('example_logger')
    >>> logger.debug('This debug message will not show.')
    >>> logger.info('This info message will show.')
    [INFO] example_logger: This info message will show.
    """
    if level.lower() not in LOG_MODES.keys():
        raise AssertionError(
            f"'{level}' is not a valid logging level. "
            + f"Choose from {list(LOG_MODES.keys())}."
        )

    numeric_level = LOG_MODES.get(level.lower(), logging.ERROR)

    if verbose:
        for lname in LOG_MODES.keys():
            arrow = "-->" if lname == level.lower() else "   "
            print(f"{arrow} {lname.upper():<10}")

    for logger_name in logging.root.manager.loggerDict:
        if logger_name.startswith("pyAMARES"):
            logger = logging.getLogger(logger_name)
            logger.setLevel(numeric_level)
