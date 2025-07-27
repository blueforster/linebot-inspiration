import logging
import sys
from datetime import datetime
from flask import Flask

def setup_logger(app: Flask):
    if not app.debug:
        # Production logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s: %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
    else:
        # Development logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(name)s: %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    # Set specific loggers
    logging.getLogger('linebot').setLevel(logging.INFO)
    logging.getLogger('gspread').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    app.logger.info("Logger configured successfully")

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)