"""Support for IP Cameras."""
import logging

from homeassistant.components.mjpeg.camera import (
    CONF_MJPEG_URL, CONF_STILL_IMAGE_URL, PLATFORM_SCHEMA, MjpegCamera, filter_urllib3_logging
)
from .const import DOMAIN, CONF_CAMERAS
from .motion_eye import MotionEye
from homeassistant.const import (CONF_HOSTS, CONF_NAME)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.info(f"motion step camera setup entry {config_entry.data}")

    meye = MotionEye(dict(config_entry.data))
    hass.data[DOMAIN][CONF_HOSTS][meye.unique_id] = meye
    await meye.load()

    cameras = []
    for cid in meye.cameras:
        meye_data = meye.cameras[cid] if cid in meye.cameras else None
        if not meye_data:
            _LOGGER.warn(f"motion step create camera missing config: {meye.unique_id}#{cid}")
            continue
        if 'enabled' in meye_data and not meye_data['enabled']:
            _LOGGER.info(f"camera not enabled: {meye_data['name']}")
            continue
        if not 'proto' in meye_data:
            _LOGGER.warn(f"motion step camera no proto: {meye_data}")
            continue
        if not meye_data['proto'] in ['motioneye', 'netcam', 'mjpeg']:
            _LOGGER.warn(f"motion step camera unknown proto {meye_data['proto']}: {meye_data}")
            continue
        _LOGGER.info(f"motion step create camera {meye.unique_id}#{cid}")
        cam = MotionEyeCamera(meye, meye_data)
        cameras.append(cam)
        hass.data[DOMAIN][CONF_CAMERAS][cam._unique_id] = cam

    async_add_entities(cameras)

class MotionEyeCamera(MjpegCamera):
    """An implementation of an IP camera that is reachable over a URL."""
    def __init__(self, motion_eye, data):
        """Initialize a MJPEG camera."""
        cid = data['id']
        self._camera_id = cid
        self._unique_id = f"{motion_eye.unique_id}_{cid}"
        still_url = motion_eye.url + motion_eye.sign('GET', f"/picture/{cid}/current/")
        if data['proto'] == 'mjpeg':
            mjpeg_url = data['url']
            still_url = mjpeg_url
        elif data['proto'] == 'motioneye':
            scheme = data["scheme"] if "scheme" in data else "http"
            mjpeg_url = f"{scheme}://{data['host']}:{data['streaming_port']}/"
        else:
            mjpeg_url = f"{motion_eye.host}:{data['streaming_port']}/"

        self._mjpeg_data = {
            CONF_NAME: data["name"],
            CONF_STILL_IMAGE_URL: motion_eye.url + motion_eye.sign('GET', f"/picture/{cid}/current/"),
            CONF_MJPEG_URL: mjpeg_url,
        }
        _LOGGER.info(f"motion step create camera mjpeg: {self._mjpeg_data}")
        super().__init__(self._mjpeg_data)
        self._actions = data['actions'] if 'actions' in data else []
        data['meye_unique_id'] = motion_eye.unique_id
        self._data = data
        self._motion_eye = motion_eye

    async def action(self, action_name):
        if not action_name in self._actions:
            _LOGGER.info(f"Invalid action {action_name} not present in {self._actions}")
            return
        _LOGGER.debug(f'Sending action: {action_name} to {self._camera_id}')
        await self._motion_eye.action(self._camera_id, action_name)

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def device_state_attributes(self):
        return {**self._mjpeg_data, **self._data}


