import logging
import requests


def get_cameras(url, username, password, verify_ssl=True):
    """Queries the Unifi Protect endpoint to return the list of cameras.

    Args:
        url (str): The hostname for the CloudKey.
        username (str): The username for the user querying the CloudKey.
        password (str): The password for the user querying the CloudKey.
        verify_ssl (bool, optional): If SSL verification should be performed
            on calls to the CloudKey instance. Defaults to True.

    Returns:
        dict: A dict containing a camera dict with the MAC address
            as the key, and two entries each for the name of the
            camera and the make of the camera.
    """
    base_url = "https://{}".format(url)
    logger.info("Getting camera list from CloudKey at {}".format(base_url))
    session = requests.Session()
    preauth = session.get(base_url, verify=verify_ssl)
    session.headers.update(
        {"X-CSRF-Token": preauth.headers['X-CSRF-Token']}
    )
    authentication = {
        "username": username, "password": password, "rememberMe": False
    }
    authentication = session.post(
        f"{base_url}/api/auth/login", data=authentication)
    bootstrap = session.get(f"{base_url}/proxy/protect/api/bootstrap")
    cameras = bootstrap.json()['cameras']
    camera_info = {}
    logger.info(f"Retrieved {len(cameras)} cameras."
    for cam in cameras:
        logger.debug(f"Adding Camera {cam['name']} - {cam['mac']}")
        camera_info[cam['mac']] = {
            "name": cam['name'],
            "type": cam['type']
        }
    logout = session.post(f"{base_url}/api/auth/logout")
    return camera_info
