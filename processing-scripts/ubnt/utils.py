import os
import sys
import urllib3
import logging
from dotenv import load_dotenv
from configparser import ConfigParser


def load_config(env_path='.env'):
    if not os.path.exists(env_path):
        raise FileNotFoundError(
            "Cannot find dotenv file {}".format(env_path)
        )
        sys.exit(1)
    else:
        load_dotenv()
        config_loaded = load_dotenv(dotenv_path=env_path)
    config = {
        "cloudkey": {
            "username": os.environ.get('CLOUDKEY_USERNAME'),
            "password": os.environ.get('CLOUDKEY_PASSWORD'),
            "controller": os.environ.get('CLOUDKEY_CONTROLLER')
        },
        "paths": {
            "ubv_files": os.environ.get('UBV_FILES'),
            "ubv_temp": os.environ.get('UBV_TEMP'),
            "ubv_output": os.environ.get('UBV_OUTPUT'),
            "ubv_archive": os.environ.get('UBV_ARCHIVE')
        }
    }
    # Determine if we should validate SSL certificates
    verify_ssl = (
        os.environ.get('CLOUDKEY_VERIFY_SSL').lower()
        in ['true', '1', 'yes', 'y']
    )
    if not verify_ssl:
        logger.warn(f"Verify SSL set to {verify_ssl}. Disabling!")
        urllib3.disable_warnings()
    else:
        logger.debug("SSL verification enabled.")
    return config, verify_ssl


def parse_arguments(args):
    # TODO - Add command line options.
    pass
