import logging
import os
import sys
import coloredlogs


LEVEL_STYLES = {
    "debug": {"color": "cyan"},
    "info": {"color": "green"},
    "warning": {"color": "yellow", "bold": True},
    "error": {"color": "red", "bold": True},
    "critical": {"color": "red", "bold": True, "underline": True},
}

FIELD_STYLES = {
    "asctime": {"color": "white", "faint": True},
    "levelname": {"bold": True},
    "name": {"color": "blue"},
}


def setup_logging(level: str | None = None) -> None:
    level = level or os.environ.get('LOG_LEVEL', 'DEBUG')

    coloredlogs.install(
        level=level,
        fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level_styles=LEVEL_STYLES,
        field_styles=FIELD_STYLES,
        isatty=True,
    )

    test_logger = logging.getLogger("test")
    test_logger.debug("debug")
    test_logger.info("info")
    test_logger.warning("warning")
    test_logger.error("error")
    test_logger.critical("critical")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
