from logging.handlers import RotatingFileHandler

from rmpc.modelling.units.data.units import Units, Unit

from rmpc.logging.formatters.custom.json import CustomJsonFormatter
from rmpc.utils.paths import get_dir, get_root_dir

log_dir = get_dir(get_root_dir().joinpath(".logs"), force_create_dir=True)

BASE_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'loggers': {
        '': {  # root logger
            'level': 'INFO',
            'handlers': [
                'debug_console_handler',
                'info_rotating_file_handler',
                'error_file_handler',
            ],
        },
        'rmpc': {
            'level': 'DEBUG',
            'propagate': False,
            'handlers': [
                'info_rotating_file_handler',
                'error_file_handler',
                'debug_console_handler',
                'rmpc_file_handler',
            ],
        },
        'rmpc.logging': {
            'level': 'INFO',
            'propagate': True,
        },
        'requests_storage': {
            'level': 'DEBUG',
            'propagate': False,
            'handlers': [
                'requests_file_handler',
            ],
        },
    },
    'handlers': {
        'debug_console_handler': {
            'level': 'DEBUG',
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
        'info_rotating_file_handler': {
            'level': 'DEBUG',
            'formatter': 'default',
            'filename': log_dir.joinpath('info.log'),
            'mode': 'a',
            'class': RotatingFileHandler,
            'maxBytes': Unit(50, Units.MB).bytes,
            'backupCount': 14,
        },
        'error_file_handler': {
            'level': 'WARNING',
            'formatter': 'detailed',
            'class': 'logging.FileHandler',
            'filename': log_dir.joinpath('error.log'),
            'mode': 'a',
        },
        'requests_file_handler': {
            'level': 'DEBUG',
            'formatter': 'json',
            'filename': log_dir.joinpath('requests.log'),
            'mode': 'a',
            'class': RotatingFileHandler,
            'maxBytes': Unit(50, Units.MB).bytes,
            'backupCount': 14,
        },
        'rmpc_file_handler': {
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': log_dir.joinpath('rmpc.log'),
            'mode': 'a',
            'class': RotatingFileHandler,
            'maxBytes': Unit(50, Units.MB).bytes,
            'backupCount': 14,
        },
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s [%(levelname)s] (%(name)s::%(module)s.%(funcName)s) : %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] (%(name)s-%(process)d::%(module)s#%(lineno)s) : %(message)s'
        },
        "json": {
            '()': CustomJsonFormatter,
            # Todo: Customize the way we control the CustomJsonFormatter / CustomJsonEncoder
        }
    },
}

__all__ = [
    'BASE_CONFIG',
]
