import logging

level_dict = {"debug": logging.DEBUG,
              "info": logging.INFO,
              "warn": logging.WARNING,
              "warning": logging.WARNING,
              "err": logging.ERROR,
              "error": logging.ERROR}


def setup_custom_logger(name, level="info"):
    formatter = logging.Formatter('%(asctime)s - %(levelname)7s - %(module)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level_dict[level])
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(handler)
    # logger.propagate = False
    return logger
