import logging
from logging.handlers import RotatingFileHandler
import time
import os

LOG_DIR = os.getenv('LOG_DIR', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE= os.path.join(LOG_DIR, "flask_app.log")

def setup_logger():
    log_rotation_size = 10 * 1024 * 1024  # 10 MB
    backup_count = 1
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='w',
    )
    handler = RotatingFileHandler(LOG_FILE, maxBytes=log_rotation_size, backupCount=backup_count)
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.WARNING) 
    logger.addHandler(handler)
    class RequestFilter(logging.Filter):
        def filter(self, record):
            if 'GET' in record.getMessage():
                return False
            return True
    logger.addFilter(RequestFilter())

def read_log_file():
    try:
        with open(LOG_FILE, 'r', buffering=1) as file:
            while True:
                line = file.readline()
                if line:
                    yield line
                else:
                    time.sleep(3)
    except Exception as e:
        yield f"Erro ao ler o arquivo: {str(e)}"

def reset_log_file():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'w') as file:
                file.truncate(0)
            return {"message": "Log successfully cleared"}
        except Exception as e:
            return {"error": str(e)}, 500

def log_message(level, message):
    logger = logging.getLogger()

    if level == 'info':
        logger.info(message)
    elif level == 'warning':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)
    elif level == 'exception':
        logger.exception(message)
    else:
        logger.debug(message)
