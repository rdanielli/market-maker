import logging
import logging.handlers
import threading
import os
import sys

initLock = threading.Lock()
rootLoggerInitialized = False

log_format = "%(asctime)s %(name)s [%(levelname)s] %(message)s"
console_log = True
console_level = logging.DEBUG
file_log = True

def init_handler(handler):
    handler.setFormatter(Formatter(log_format))

def init_logger(logger):
    logger.setLevel(logging.DEBUG)

    if file_log:
        path = os.path.dirname(__file__) + "\logs"
        file_level = logging.INFO
        fileHandler = logging.handlers.RotatingFileHandler(path+"\info.logs", maxBytes=10485760, backupCount=5)
        fileHandler.setLevel(file_level)
        init_handler(fileHandler)
        logger.addHandler(fileHandler)

        warning_level = logging.WARNING
        fileWarningHandler = logging.handlers.RotatingFileHandler(path+"\warning.logs", maxBytes=10485760, backupCount=5)
        fileWarningHandler.setLevel(warning_level)
        init_handler(fileWarningHandler)
        logger.addHandler(fileWarningHandler)

    if console_log:
        # sys.stdout is used so that doctest is able to read output produced by logging.
        # Standard is to leave it empty which means sys.stderr
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setLevel(console_level)
        init_handler(consoleHandler)
        logger.addHandler(consoleHandler)

def initialize():
    global rootLoggerInitialized
    with initLock:
        if not rootLoggerInitialized:
            init_logger(logging.getLogger())
            rootLoggerInitialized = True

def getLogger(name=None):
    initialize()
    return logging.getLogger(name)

# This formatter provides a way to hook in formatTime.
class Formatter(logging.Formatter):
    DATETIME_HOOK = None

    def formatTime(self, record, datefmt=None):
        newDateTime = None

        if Formatter.DATETIME_HOOK is not None:
            newDateTime = Formatter.DATETIME_HOOK()

        if newDateTime is None:
            ret = logging.Formatter.formatTime(self, record, datefmt)
        else:
            ret = str(newDateTime)
        return ret
