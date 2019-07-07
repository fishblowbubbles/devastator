import argparse
import pickle
import socket

from evdev import InputDevice, categorize, ecodes, list_devices

import romeo

DEVICE_NAME = "Microsoft X-Box One S pad"

L_JS_X, L_JS_Y, L_TRIG = 0, 1, 2
R_JS_X, R_JS_Y, R_TRIG = 3, 4, 5
DPAD_X, DPAD_Y = 16, 17
A_BTN, B_BTN = 304, 305
X_BTN, Y_BTN = 307, 308
L_BUMP, R_BUMP = 310, 311
SELECT, START = 314, 315

JS_MIN, JS_MAX, JS_THRESH = -32768, 32767, 0.1
TRIG_MAX = 1023

BTN_UP, BTN_DOWN = 0, 1
DPAD_UP, DPAD_DOWN = 1, -1


class XPad:
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

    def run(self):
        for event in self.device.read_loop():
            if event.type in [ecodes.EV_KEY, ecodes.EV_ABS]:
                command = (event.code, event.value)
                romeo.send_command(command)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-name", default=DEVICE_NAME)
    args = parser.parse_args()

    xpad = XPad(device_name=args.device_name)
    xpad.run()
