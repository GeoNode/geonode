import logging

DEFAULT_COMMAND_LOGGER_NAME = "geonode.commands"


def setup_logger(logger_name=DEFAULT_COMMAND_LOGGER_NAME, level=logging.INFO, **kwargs):
    logger = logging.getLogger(logger_name)

    # remove previous handlers
    for old_handler in logger.handlers:
        logger.removeHandler(old_handler)

    format = "%(levelname)-7s %(asctime)s %(message)s"

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt=format))
    handler.setLevel(level)

    logger.addHandler(handler)

    logger.setLevel(level)
    logger.propagate = False

    return logger
