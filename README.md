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

**Example**: A Raspberry Pi with _MotionEyeOS_ installed will have a web UI on port 80. I have multiple Raspberry Pi Zero Ws, and I just add each as a separate integration to Home Assistant. Their configuration URLs are `http://192.168.0.161`, etc.

If you're trying to connect to a MotionEye instance between Docker containers (or Kubernetes pods), you need to make sure that the Home Assistant instance can access the target URL. For example, you should be able to to `curl http://192.168.0.161`. I happen to run Kubernetes for all of my home automation, so I actually use the URL `http://motion.home.svc.cluster.local:8765` for one of my integrations.

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
