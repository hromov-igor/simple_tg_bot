import logging
from logging.handlers import RotatingFileHandler


def setup_logging(name: str = "simple_tg_bot", level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        fh = RotatingFileHandler("bot.log", maxBytes=1_000_000, backupCount=3)
        fh.setFormatter(fmt)
        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger
