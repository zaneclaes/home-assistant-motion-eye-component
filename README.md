# Home Assistant Motion Eye Component

Upgraded MotionEye support for Home Assistant.

See a [complete example and use-case here](https://www.technicallywizardry.com/pan-tilt-zoom-security-camera/).

* Automatic discovery of cameras.
* Trigger camera actions with Home Assistant events.

![Pan Tilt Zoom Security Camera](https://content.technicallywizardry.com/2020/07/14145657/pan-tilt-zoom-security-camera-home-assistant-card.jpg)

## Configuration Sample

The component can be installed via the Home Assistant UI.

```
motion_eye:
  hosts:
    - url: "http://motion-eye.local"
      username: !secret motion_username
      password: !secret motion_password
```

Upon restart, Home Assistant will automatically create `camera` entities for each camera found at `http://motion-eye.local` with the appropriate MotionEye camera name.  Each camera entity will contain all of the MotionEye camera attributes.

Examples:

* **MotionEyeOS**: A Raspberry Pi with _MotionEyeOS_ installed will have a web UI on port 80. I have multiple Raspberry Pi Zero Ws, and I just add each as a separate integration to Home Assistant. Their configuration URLs are `http://192.168.0.161`, etc.
* **MotionEye Add-On (Supervisor)**: The easiest approach is to tweak the HA add-on configuration to allow access. From the `Configuration` tab in the `Network` section, choose a host port, say, 8081. After restarting, you should be able to access the MotionEye UI using the static IP of your Home Assistant device and the port you have chosen. For example, `http://192.168.0.100:8081` (note I used the IP and not `homeassistant.local`). This is the correct `url` setting.
* **Docker/Kubernetes**: If you're trying to connect to a MotionEye instance between Docker containers (or Kubernetes pods), you need to make sure that the Home Assistant instance can access the target URL. I happen to run Kubernetes for all of my home automation, so I actually use the URL `http://motion.home.svc.cluster.local:8765` for one of my integrations, as this is the syntax for intra-service DNS lookups.

**When in doubt** you can use your browser's "Network Inspector" feature while using MotionEye.

![network inspector](https://content.technicallywizardry.com/2020/07/15122339/Screen-Shot-2020-07-15-at-6.22.13-AM-1024x519.jpg)

In the above screenshot, the correct configuration URL would be `https://cameras.snowy-cabin.com` (everything before the `/picture`...)

## Using the Components

_I am using my workshop camera as an example, which has a built-in PAN-TILT hat._

### List Available Actions

```
{{ states.camera.workshop.attributes.actions }}
```

The actions are printed by the template editor:

```
['snapshot', 'up', 'down', 'left', 'right']
```

### Send an Action

Fire the `motion_eye_action` event with the following parameters:

```
camera_id: camera.workshop
action: up
```

Where `camera_id` is from this example, and `up` was a known action from the prior step.

For convenience, I wrapped this into a script:

```
script:
  motion_eye_action:
    alias: Motion Eye - Call Action
    sequence:
    - event: motion_eye_action
      event_data_template:
        camera_id: "{{ camera_id }}"
        action: "{{ action }}"
```

### Lovelace Card

It's nice to have action buttons in a picture glance card.

```
title: "Workshop"
camera_image: 'camera.workshop'
entities:
  - entity: 'camera.workshop'
    icon: 'mdi:arrow-left'
    tap_action:
      action: call-service
      service: script.motion_eye_action
      service_data:
        action: left
        camera_id: 'camera.workshop'
  - entity: 'camera.workshop'
    icon: 'mdi:arrow-right'
    tap_action:
      action: call-service
      service: script.motion_eye_action
      service_data:
        action: right
        camera_id: 'camera.workshop'
  - entity: 'camera.workshop'
    icon: 'mdi:arrow-up'
    tap_action:
      action: call-service
      service: script.motion_eye_action
      service_data:
        action: up
        camera_id: 'camera.workshop'
  - entity: 'camera.workshop'
    icon: 'mdi:arrow-down'
    tap_action:
      action: call-service
      service: script.motion_eye_action
      service_data:
        action: down
        camera_id: 'camera.workshop'
  - entity: 'security_feed.workshop'
aspect_ratio: 0%
type: picture-glance
```

### Tidying Up

It's a bit annoying to manually code all the actions. I haven't found a good way to templatize a Lovelace card with a `for-loop` style iteration of the actions yet. However, if you want to use a [config template card](https://github.com/iantrich/config-template-card) you potentially use positional matching against the known set of actions to selectivly enable the required buttons. [Let me know](https://www.technicallywizardry.com/contact/) if you get that, or anything else working. Failing that, it would probably be easiest to add a custom card with this component.

## Installation

See the Releases tab to find the current version. Download the source code and move the directory to a folder named `motion_eye` in the Home Assistant custom component directory. For example, `config/custom_components/motion_eye` should contain all of the source code in this repository.

## Technical Details

This custom component interacts with the undocumented MotionEye API. The `motion_eye.py` file signs the requests, allowing it to query for the list of cameras. The Home Assistant `camera` entity inherits from the `mjpeg` camera, and assigns the appropriate attributes for stills and streams. Events are handled and translated into `POST` requests to the appropriate `action` endpoint.

## Supported Cameras

I have tested this with:

* `Local VL2 Camera`
* `Network Camera`
* `Remote MotionEye Camera`
* `Simple MJPEG Camera`

## Supported MotionEye Installs

I have tested connecting to MotionEye instances of the following kinds:

* _MotionEyeOS_ (pre-built image for Raspberry Pis)
* _MotionEye Home Assistant Supervisor Add-On_
* _MotionEye Docker container in Kubernetes_

