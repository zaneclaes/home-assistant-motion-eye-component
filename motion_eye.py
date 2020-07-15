import logging
import asyncio
import hashlib
import urllib.parse as urlparse
import requests
import re
import time
from homeassistant.helpers import aiohttp_client, config_validation as cv
from .const import DOMAIN
from homeassistant.const import (CONF_NAME, CONF_URL, CONF_USERNAME, CONF_PASSWORD, CONF_AUTHENTICATION)

_SIGNATURE_REGEX = re.compile('[^a-zA-Z0-9/?_.=&{}\[\]":, -]')
_LOGGER = logging.getLogger(__name__)

class MotionEye():
    """Class to connect to a single MotionEye host."""
    def __init__(self, config):
        """Assumes config confirms to const.MOTION_SCHEMA"""
        self._url = config[CONF_URL]
        if self._url.endswith('/'): self._url = self._url[0:-1]
        self._unique_id = cv.slugify(self._url)
        self._username = config[CONF_USERNAME]
        self._password = config[CONF_PASSWORD]
        self._auth = config[CONF_AUTHENTICATION]
        self._pwhash = hashlib.sha1(self._password.encode('utf-8')).hexdigest()
        self._session = requests.Session()
        self._cameras = {}
        o = urlparse.urlparse(self._url)
        self._host = o.scheme + '://' + o.hostname
        self._path = o.path
        _LOGGER.info(f"step motion created API {self.unique_id} -> {self._host} {self._path}")

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def title(self):
        return "MotionEye " + self._url

    @property
    def host(self):
        return self._host

    @property
    def url(self):
        return self._url

    # Config which can be directly inherited by a mjpeg camera.
    @property
    def camera_config(self):
        return {
            CONF_USERNAME: self._username,
            CONF_PASSWORD: self._password,
            CONF_AUTHENTICATION: self._auth,
        }

    @property
    def cameras(self):
        return self._cameras

    # Load the initial set of cameras, to be tuned into MotionEyeCamera obects.
    async def load(self):
        """Load the cameras from MotionEye"""
        _LOGGER.info(f'Connecting to MotionEye at {self._host}')
        res = await self.get('/config/list/')
        cameras = res['cameras'] if res and 'cameras' in res else []
        self._cameras = {}
        for cam in cameras:
            self._cameras[cam['id']] = cam
        return self._cameras

    # Trigger a MotionEye action.
    async def action(self, camera_id, action):
        return await self.post(f'/action/{camera_id}/{action}/')

    # Perform a GET request.
    async def get(self, path, qps = {}):
        url = self._url + self.sign('GET', path, qps)
        _LOGGER.info(f'MotionEye API GET: {url}')
        future = asyncio.get_event_loop().run_in_executor(None, self._session.get, url)
        return await self._decode_response(future)

    # Perform a POST request.
    async def post(self, path, body=None, qps = {}):
        url = self._url + self.sign('POST', path, qps, body)
        _LOGGER.info(f'MotionEye API POST: {url}')
        future = asyncio.get_event_loop().run_in_executor(None, self._session.post, url, body)
        return await self._decode_response(future)

    # Responses should be JSON. If not, or not successful, throw an error.
    async def _decode_response(self, future):
        try:
            res = await future
            _LOGGER.info(f'MotionEye API Response [{res.status_code}]: {res.text}')
            if res.status_code != 200:
                _LOGGER.error(f'MotionEye API was unsuccessful [{res.status_code}]: {res.text}')
                return None
            return res.json()
        except Exception as e:
            _LOGGER.error(f'MotionEye API returned an invalid response: {e}')
            return None

    # Public method for turning a path into a signed path (for making authenticated requests).
    # @return a string representing the path
    def sign(self, method, path, qps = {}, body = None):
        qps['_'] = int(time.time())
        qps['_username'] = self._username
        path += '?' + '&'.join([f'{x}={qps[x]}' for x in qps])
        path += '&_signature=' + self._compute_signature(method, path, body)
        return path

    # Copied from MotionEye backend.
    # c.f. https://github.com/ccrisan/motioneye/blob/3b9d110d09369e4520f03126977eb81a606393df/motioneye/utils.py#L668
    def _compute_signature(self, method, path, body = None):
        if not '_username=' in path:
            if not '?' in path: path += '?'
            else: path += '&'
            path += f'_username={self._username}'
        _LOGGER.info(f'MotionEye API signing "{method}" "{path}"')
        key = self._pwhash
        parts = list(urlparse.urlsplit(path))
        query = [q for q in urlparse.parse_qsl(parts[3], keep_blank_values=True) if (q[0] != '_signature')]
        query.sort(key=lambda q: q[0])
        # "safe" characters here are set to match the encodeURIComponent JavaScript counterpart
        query = [(n, urlparse.quote(v, safe="!'()*~")) for (n, v) in query]
        query = '&'.join([(q[0] + '=' + q[1]) for q in query])
        parts[0] = parts[1] = ''
        parts[3] = query
        path = urlparse.urlunsplit(parts)
        path = _SIGNATURE_REGEX.sub('-', path)
        key = _SIGNATURE_REGEX.sub('-', key)

        if body and body.startswith('---'):
            body = None  # file attachment

        body = body and _SIGNATURE_REGEX.sub('-', body.decode('utf8'))

        return hashlib.sha1(('%s:%s:%s:%s' % (method, path, body or '', key)).encode('utf-8')).hexdigest().lower()

    @property
    def host(self):
        return self._host
