
import json, logging, os, sys, time, threading

_LEVEL = os.getenv("LOG_LEVEL","INFO").upper()
LEVEL = getattr(logging, _LEVEL, logging.INFO)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "ts": int(time.time()*1000),
            "lvl": record.levelname,
            "msg": record.getMessage(),
            "name": record.name,
            "thread": threading.current_thread().name,
        }
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)

def get_logger(name: str):
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(JsonFormatter())
        logger.addHandler(h)
        logger.setLevel(LEVEL)
    return logger
