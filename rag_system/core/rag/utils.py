import logging

logger = logging.getLogger(__name__)

def log_error(msg):
    logger.exception(msg)