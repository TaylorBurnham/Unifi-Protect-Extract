import os
import sys
import logging
from dotenv import load_dotenv


def _check_boolean(x):
    return x.lower() in ['true', '1', 'yes', 'y']


class Config():
    def __init__(self, dotenv='.env'):
        self.dotenv = dotenv
        self._load_dotenv()
        self.paths = PathCfg()
        self.cloudkey = CloudKeyCfg()
        self.logs = LogCfg()

    def _load_dotenv(self):
        if not os.path.exists(self.dotenv):
            raise FileNotFoundError(f"Cannot find dotenv at {self.dotenv}")
            sys.exit(1)
        else:
            load_dotenv(dotenv_path=self.dotenv)


class PathCfg():
    def __init__(self):
        self.files = os.environ.get('UBV_FILES')
        self.temp = os.environ.get('UBV_TEMP')
        self.output = os.environ.get('UBV_OUTPUT')
        self.min_age = int(os.environ.get("UBV_MIN_AGE"))


class CloudKeyCfg(object):
    def __init__(self):
        self.username = os.environ.get('CLOUDKEY_USERNAME')
        self.password = os.environ.get('CLOUDKEY_PASSWORD')
        self.controller = os.environ.get('CLOUDKEY_CONTROLLER')
        self.ssl = _check_boolean(
            os.environ.get('CLOUDKEY_VERIFY_SSL'))


class LogCfg(object):
    def __init__(self):
        self.enabled = _check_boolean(
            os.environ.get('LOGGING_ENABLED'))
        self.logfile = _check_boolean(
            os.environ.get('LOGGING_TO_FILE'))
        self.format = os.environ.get('LOGGING_FORMAT')
        self.level = logging.getLevelName(
            os.environ.get('LOGGING_LEVEL')
        )
