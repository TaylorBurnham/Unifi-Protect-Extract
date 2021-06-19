import sys
import urllib3
import requests
import logging


class CloudKey():
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.logger.info("CloudKey Class Initialized")
        self.url = "https://{}".format(self.config.controller)
        self.verify_ssl = self._check_ssl()

    def _check_ssl(self):
        if self.config.ssl:
            self.logger.debug(
                f"Connecting to {self.config.controller} with SSL."
            )
        else:
            self.logger.warning(
                f"Connecting to {self.config.controller} without SSL."
            )
            self.logger.warning(
                "You should really configure SSL with letsencrypt. "
                "It's really easy. I swear."
            )
            urllib3.disable_warnings()
        return self.config.ssl

    def get_bootstrap(self):
        self.logger.debug(
            f"Querying CloudKey at {self.url}"
        )
        session = requests.Session()
        preauth = session.get(self.url, verify=self.verify_ssl)
        session.headers.update(
            {"X-CSRF-Token": preauth.headers['X-CSRF-Token']}
        )
        authentication = {
            "username": self.config.username,
            "password": self.config.password,
            "rememberMe": False
        }
        auth = session.post(  # noqa: F841
            f"{self.url}/api/auth/login", data=authentication
        )
        if auth.status_code != 200:
            self.logger.critical(
                f"Status Code {auth.status_code} raised on "
                "authentication attempt. Bad password?"
                "Exiting..."
            )
            sys.exit(1)
        else:
            bootstrap = session.get(
                f"{self.url}/proxy/protect/api/bootstrap"
            )
            deauth = session.post(  # noqa: F841
                f"{self.url}/api/auth/logout"
            )
            self.logger.debug(
                "Returning bootstrap data from cloudkey."
            )
            cameras = bootstrap.json()
        return cameras

    def get_cameras(self):
        self.logger.info("Getting Cameras")
        bootstrap = self.get_bootstrap()
        camera_list = {}
        for camera in bootstrap['cameras']:
            self.logger.debug(
                f"Adding Camera {camera['name']} - {camera['mac']}."
            )
            camera_list[camera['mac']] = {
                "name": camera['name'],
                "type": camera['type']
            }
        self.logger.info(
            f"Returning {len(camera_list)} cameras."
        )
        return camera_list
