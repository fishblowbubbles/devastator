import argparse
import pickle
import socket

from evdev import InputDevice, categorize, ecodes, list_devices

from romeo import send_command

DEVICE_NAME = "MICROSOFT X-BOX ONE S PAD"


class XboxOneSPad:
    def __init__(self, device_name=DEVICE_NAME):
        self.device_name = device_name
        self._set_device(device_name)

    def _set_device(self, device_name):
        for path in list_devices():
            device = InputDevice(path)
            if device.name.upper() == device_name:
                self.device = device
                break
        else:
            msg = "{} not found".format(device_name)
            raise Exception(msg)

    def _handle_event(self, event):
        if event.type in [ecodes.EV_KEY, ecodes.EV_ABS]:
            command = (event.code, event.value)
            send_command(command)

    def run(self):
        while True:
            for event in self.device.read_loop():
                self._handle_event(event)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-name", default=DEVICE_NAME)
    args = parser.parse_args()

    controller = XboxOneSPad()
    controller.run()
