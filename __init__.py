# http://motion.home.svc.cluster.local:8765/
# /movie/3/list/?prefix=2020-04-18&_=1587579711596&_username=admin&_signature=f11212098f8a1d4f60a60ba3bdc1b3f29214a421'
# /movie/3/delete/2020-04-18/16-36-35.mp4?_=1587579940905&_username=admin&_signature=7f446401f34d53568343912eb132b9ed075d0313'
# /config/list

"""The example integration."""
import voluptuous as vol
import logging
import homeassistant.core as ha
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, MOTION_EYE_SCHEMA, CONF_CAMERAS
from homeassistant import config_entries
from .motion_eye import MotionEye
from homeassistant.const import (CONF_HOSTS, CONF_ID, CONF_URL, CONF_AUTHENTICATION, CONF_USERNAME, CONF_PASSWORD)
# from homeassistant import config_entries

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        CONF_HOSTS: [MOTION_EYE_SCHEMA]
    })
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Set up the MotionEye component."""
    hass.data.setdefault(DOMAIN, {})
    conf = config.get(DOMAIN)
    hosts = conf.get(CONF_HOSTS, []) if conf else []
    hass.data[DOMAIN][CONF_HOSTS] = {}
    hass.data[DOMAIN][CONF_CAMERAS] = {}

    existing = {
        entry.data.get(CONF_URL) : entry for entry in hass.config_entries.async_entries(DOMAIN)
    }

    for host in hosts:
        data = dict(host)
        _LOGGER.info(f"motion step init setup {data}")
        if CONF_URL in data and data[CONF_URL] in existing:
            entry = existing[data[CONF_URL]]
            _LOGGER.info(f"motion step init update {data}")
            hass.config_entries.async_update_entry(entry, data=data)
        else:
            _LOGGER.info(f"motion step init create {data}")
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=data
                )
            )

    @ha.callback
    async def handle_motion_eye_action(event):
        _LOGGER.info(f"motion eye action {event}")
        camera_id = event.data.get('camera_id')
        action = event.data.get('action')
        if not camera_id:
            _LOGGER.error('missing parameter: camera_id')
            return
        if not action:
            _LOGGER.error('missing parameter: action')
            return
        cam = hass.states.get(camera_id)
        if not cam:
            _LOGGER.error(f'invalid camera ID: {camera_id}')
            return
        _LOGGER.info(f"motion {cam.attributes['meye_unique_id']} #{cam.attributes['id']} action: {action}")
        meye = hass.data[DOMAIN][CONF_HOSTS][cam.attributes['meye_unique_id']]
        res = await meye.action(cam.attributes['id'], action)
        _LOGGER.info(f"#{cam.attributes['id']} action {action} result: {res}")

    hass.bus.async_listen(f'{DOMAIN}_action', handle_motion_eye_action)

    return True

async def async_setup_entry(hass, entry: config_entries.ConfigEntry):
    """Set up camera from a config entry."""

    # hosts = conf.get(CONF_HOSTS, []) if conf else []
    # websession = aiohttp_client.async_get_clientsession(hass)
    _LOGGER.info(f"motion step init setup entry {entry.as_dict()}")
    opts = entry.data
    url = opts.get(CONF_URL, '')
    if len(url) <= 0:
        _LOGGER.error(f"Invalid configuration for entry: {entry.as_dict()}")
        return False

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "camera")
    )
    return True
