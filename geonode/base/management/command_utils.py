import logging
from django.conf import settings

DEFAULT_COMMAND_LOGGER_NAME = "geonode.commands"


def setup_logger(logger_name=DEFAULT_COMMAND_LOGGER_NAME, formatter_name="command", handler_name="command"):
    if logger_name not in settings.LOGGING["loggers"]:
        format = "%(levelname)-7s %(asctime)s %(message)s"

        settings.LOGGING["formatters"][formatter_name] = {
            "format": format
        }
        settings.LOGGING["handlers"][handler_name] = {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": formatter_name
        }
        settings.LOGGING["loggers"][logger_name] = {
            "handlers": [handler_name],
            "level": "INFO",
            "propagate": False
        }

        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt=format))
        handler.setLevel(logging.DEBUG)

        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

        return logger
