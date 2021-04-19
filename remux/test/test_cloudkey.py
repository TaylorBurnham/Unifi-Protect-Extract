import os
import sys
import json
import logging
import unittest
from unittest.mock import patch
from utilities.config import Config
from utilities.cloudkey import CloudKey


def _load_boostrap(basepath):
    filepath = os.path.join(
        basepath, 'test_data', 'bootstrap.json'
    )
    if os.path.exists(filepath):
        with open(filepath, 'r') as fh:
            data = json.load(fh)
    else:
        print(f"Can't find bootstrap file at {filepath}")
        sys.exit(1)
    return data


class TestCloudKey(unittest.TestCase):
    def setUp(self):
        self.path = os.path.dirname(os.path.realpath(__file__))
        self.config = Config(
            dotenv=os.path.join(self.path, '.env.testing')
        )
        self.cloudkey = CloudKey(config=self.config.cloudkey)

    def test_get_cameras(self):
        tmp_bs = _load_boostrap(self.path)
        with patch(
            'utilities.cloudkey.CloudKey.get_bootstrap',
            return_value=tmp_bs
        ) as p:  # noqa: F841
            camera_list = self.cloudkey.get_cameras()
        self.assertTrue(
            "B4FBE48C5F9E" in camera_list
        )
        self.assertTrue(
            "B4FBE4FBC66F" in camera_list
        )
        self.assertTrue(
            "Front Yard" == camera_list['B4FBE4FBC66F']['name']
        )
        self.assertTrue(
            "UVC G3" == camera_list['B4FBE4FBC66F']['type']
        )


if __name__ == "__main__":
    logger = logging.getLogger()
    logging_handler = logging.StreamHandler(sys.stdout)
    log_format = '[%(asctime)s] {%(filename)s:%(lineno)d} ' \
        '%(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=[logging_handler]
    )
    logger.info("Initialized.")
    unittest.main(verbosity=3)
