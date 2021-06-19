import os
import sys
import json
import logging
import unittest
from unittest.mock import patch
from datetime import date
from utilities.config import Config
from utilities.cloudkey import CloudKey
from utilities.processing import UBVRemux


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


def _load_testdata(basepath):
    filepath = os.path.join(
        basepath, 'test_data', 'test_files.json'
    )
    if os.path.exists(filepath):
        with open(filepath, 'r') as fh:
            data = json.load(fh)
    else:
        print(f"Can't find test data file at {filepath}")
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


class TestRemux(unittest.TestCase):
    def setUp(self):
        self.path = os.path.dirname(os.path.realpath(__file__))
        self.config = Config(
            dotenv=os.path.join(self.path, '.env.testing')
        )
        # Remap config paths
        self.config.paths.files = os.path.join(
            self.path, self.config.paths.files)
        self.config.paths.temp = os.path.join(
            self.path, self.config.paths.temp)
        self.config.paths.output = os.path.join(
            self.path, self.config.paths.output)
        self.cloudkey = CloudKey(config=self.config.cloudkey)
        self.remux = UBVRemux(
            config=self.config.paths, auto_create_tmp=False)
        tmp_bs = _load_boostrap(self.path)
        with patch(
            'utilities.cloudkey.CloudKey.get_bootstrap',
            return_value=tmp_bs
        ) as p:  # noqa: F841
            self.cameras = self.cloudkey.get_cameras()
        self.test_data = _load_testdata(self.path)

    def test_mp4_parse(self):
        mp4dict = self.remux.parse_mp4(
            self.test_data['mp4_file'], self.cameras
        )
        output_path = mp4dict['output']['path']
        output_file = mp4dict['output']['filename']
        expected_path = os.path.join(
            self.config.paths.output, '2021-01-27', 'Hallway'
        )
        self.assertEqual(
            output_path, expected_path
        )
        self.assertTrue(
            output_file.startswith('Hallway_')
            and output_file.endswith('.mp4')
        )
        self.assertEqual(
            output_file, "Hallway_2021-01-27_18-04-53.mp4"
        )

    def test_mp4_move(self):
        # TODO
        pass

    def test_get_ubv_files(self):
        ubv_files = self.remux.get_ubv_files(
            self.config.paths.files
        )
        self.assertTrue(
            date(2021, 1, 27) in ubv_files
        )
        self.assertTrue(
            date(2021, 2, 1) in ubv_files
        )
        # Should have three files
        files = len([
            x for x in ubv_files[date(2021, 1, 27)]
        ])
        self.assertEqual(
            files, 3
        )
        # Check our prepared file count for 27-Jan
        prepped = len([
            x for x in ubv_files[date(2021, 1, 27)] if x['prepared']
        ])
        self.assertEqual(
            prepped, 2
        )
        # Check our muxed files
        muxed = len([
            x for x in ubv_files[date(2021, 1, 27)] if x['muxed']
        ])
        self.assertEqual(
            muxed, 1
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
