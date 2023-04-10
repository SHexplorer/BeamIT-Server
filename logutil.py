import logging
import os
from datetime import datetime



def init(level):
    if not os.path.exists("./log"):
        os.makedirs("./log")

    if level == "debug":
        level = logging.DEBUG
    if level == "error":
        level = logging.ERROR
    if level == "info":
        level = logging.INFO
    
    logger = logging.getLogger("log")
    logger.setLevel(level)
    l1 = logging.StreamHandler()
    l1.setLevel(level)
    l2 = logging.FileHandler(filename="./log/beamit-server-" + datetime.now().strftime('%Y-%m-%d') + ".log")
    l2.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(funcName)s - %(levelname)s - %(message)s')
    #formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
    l1.setFormatter(formatter)
    l2.setFormatter(formatter)
    logger.addHandler(l1)
    logger.addHandler(l2)

    return logger

if __name__ == '__main__':
    logger = init("debug")
    logger.debug("debug")
    logger.error("error")
    logger.warning("waring")
    logger.info("info")