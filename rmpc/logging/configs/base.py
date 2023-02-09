from pathlib import Path

from rmpc.logging.formatters.custom.json import CustomJsonFormatter
from rmpc.modelling.units.data.units import Units, Unit
from rmpc.utils.paths import get_dir, get_root_dir

log_dir = get_dir(
    get_root_dir(
        match_first_git_dir=True, expected_root_names=[__package__.split(".")[0]]
    ).joinpath(".logs/"),
    force_create_dir=True,
)

log_fmt = "%(asctime)s [%(levelname)s] (%(name)s.%(funcName)s:%(lineno)s) : %(message)s"
log_datefmt = "%Y-%m-%d %H:%M:%S"


def make_rotating_handler_definition(**kwargs):
    kwargs.setdefault("level", "DEBUG")
    kwargs.setdefault("formatter", "default")
    kwargs.setdefault("class", "logging.handlers.RotatingFileHandler")
    kwargs.setdefault("mode", "a")
    kwargs.setdefault("maxBytes", Unit(50, Units.MB).bytes)
    kwargs.setdefault("backupCount", 14)
    fname = kwargs.setdefault("filename", "")

    if not isinstance(fname, Path):
        fname = Path(fname)

    if log_dir not in fname.parents:
        kwargs["filename"] = log_dir.joinpath(fname)

    return {
        k: v
        for k, v in kwargs.items()
        if k
        in [
            "level",
            "formatter",
            "filename",
            "class",
            "mode",
            "maxBytes",
            "backupCount",
        ]
    }


BASE_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "loggers": {
        "": {  # root logger
            "level": "INFO",
            "handlers": [
                "debug_console_handler",
                "info_rotating_file_handler",
                "error_file_handler",
            ],
        },
        "rmpc": {
            "level": "DEBUG",
            "propagate": False,
            "handlers": [
                "debug_console_handler",
                "info_rotating_file_handler",
                "error_file_handler",
                "internal_file_handler",
            ],
        },
        # "rmpc.logging": {
        #     "level": "INFO",
        #     "propagate": True,
        # },
        "requests_storage": {
            "level": "DEBUG",
            "propagate": False,
            "handlers": [
                "requests_file_handler",
            ],
        },
    },
    "handlers": {
        "debug_console_handler": {
            "level": "DEBUG",
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "info_rotating_file_handler": make_rotating_handler_definition(
            level="DEBUG",
            formatter="default",
            filename=log_dir.joinpath("info.log"),
        ),
        "error_file_handler": make_rotating_handler_definition(
            level="WARNING",
            formatter="detailed",
            filename=log_dir.joinpath("error.log"),
        ),
        "requests_file_handler": make_rotating_handler_definition(
            level="INFO",
            formatter="json_simple",
            filename=log_dir.joinpath("requests.log"),
        ),
        "internal_file_handler": make_rotating_handler_definition(
            level="DEBUG",
            formatter="detailed",
            filename=log_dir.joinpath("internal.log"),
        ),
    },
    "formatters": {
        "default": {
            "format": log_fmt,
            "datefmt": log_datefmt,
        },
        "detailed": {
            "format": log_fmt,
            "datefmt": log_datefmt,
        },
        "json_simple": {
            "()": CustomJsonFormatter,
            "datefmt": log_datefmt,
            "disable_extra_fields": True,
        },
        "json_detailed": {
            "()": CustomJsonFormatter,
            "datefmt": log_datefmt,
        },
    },
}

__all__ = [
    "BASE_CONFIG",
]
