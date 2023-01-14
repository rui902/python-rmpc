import logging
import logging.config
import os

from .configs.base import BASE_CONFIG

LOG_CONF_SOURCE = None

log_config_file = os.environ.get(
    "LOG_CONF_FILE", os.environ.get(
        "LOG_CONF_FILE",
        None
    )
)
if log_config_file and not os.path.exists(log_config_file):
    log_config_file_path = os.path.join(os.path.dirname(__file__), log_config_file)
    if os.path.exists(log_config_file_path):
        log_config_file = log_config_file_path

if log_config_file:
    logging.config.fileConfig(log_config_file, encoding="utf-8")
    LOG_CONF_SOURCE = (logging.config.fileConfig, log_config_file)

else:
    logging.config.dictConfig(BASE_CONFIG)
    LOG_CONF_SOURCE = (logging.config.dictConfig, BASE_CONFIG)


def get_logger(logger_name: str = None):
    logger = logging.getLogger(logger_name)

    return logger


root_logger = get_logger()
pkg_root = get_logger(__name__.split(".")[0])

__all__ = [
    'root_logger',
    'pkg_root',
    'get_logger',
    'LOG_CONF_SOURCE',
]
