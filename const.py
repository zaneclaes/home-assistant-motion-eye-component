import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.const import (CONF_HOSTS, CONF_URL, CONF_AUTHENTICATION, CONF_USERNAME, CONF_PASSWORD)

DOMAIN = "motion_eye"
CONF_CAMERAS = "cameras"

MOTION_EYE_SCHEMA = vol.Schema({
    vol.Required(CONF_URL, default=""): str,
    vol.Optional(CONF_AUTHENTICATION, default="basic"): str,
    vol.Required(CONF_USERNAME, default="admin"): str,
    vol.Required(CONF_PASSWORD, default=""): str,
})

MOTION_EYE_PLACEHOLDERS = {
    CONF_URL: "URL for MotionEye",
    CONF_AUTHENTICATION: "",
    CONF_USERNAME: "MotionEye username",
    CONF_PASSWORD: "MotionEye password",
}