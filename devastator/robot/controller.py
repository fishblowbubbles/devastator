import argparse
import pickle
import socket

from evdev import InputDevice, categorize, ecodes, list_devices

import romeo

DEVICE_NAME = "Microsoft X-Box One S pad"


class XboxOneSPad:
    def __init__(self, device_name=DEVICE_NAME):
        self.device = self._get_device(device_name)

    def _get_device(self, device_name):
        for path in list_devices():
            device = InputDevice(path)
            if device.name == device_name:
                return device
        else:
            message = "{} not found".format(device_name)
            raise Exception(message)

    def _handle_event(self, event):
        if event.type in [ecodes.EV_KEY, ecodes.EV_ABS]:
            command = (event.code, event.value)
            romeo.send_command(command)

    def run(self):
        while True:
            for event in self.device.read_loop():
                self._handle_event(event)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-name", default=DEVICE_NAME)
    args = parser.parse_args()

    xpad = XboxOneSPad(device_name=args.device_name)
    xpad.run()
