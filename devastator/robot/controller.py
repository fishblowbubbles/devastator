import argparse

from evdev import InputDevice, categorize, ecodes, list_devices

HOST = "127.0.0.1"
PORT = 8888

DEVICE_NAME = "MICROSOFT X-BOX ONE S PAD"

BTN_UP, BTN_DN = 0, 1

L_JS_X, L_JS_Y, L_TRIG = 0, 1, 2
R_JS_X, R_JS_Y, R_TRIG = 3, 4, 5
DPAD_X, DPAD_Y = 16, 17
A_BTN, B_BTN = 304, 305
X_BTN, Y_BTN = 307, 308
L_BUMP, R_BUMP = 310, 311
SELECT, START = 314, 315

JS_MIN, JS_MAX = -32768, 32767
TRIG_MAX = 1023


class XboxOneSPad:
    def __init__(self, device_name=DEVICE_NAME, host=HOST, port=PORT):
        self.host, self.port = host, port
        self.device_name = device_name
        self._set_device(device_name)
        self.callbacks = {
            L_JS_X: self._handle_left_joystick_x,
            L_JS_Y: self._handle_left_joystick_y,
            L_TRIG: self._handle_left_trigger,
            L_BUMP: self._handle_left_bumper,
            R_JS_X: self._handle_right_joystick_y,
            R_JS_Y: self._handle_right_joystick_y,
            R_TRIG: self._handle_right_trigger,
            R_BUMP: self._handle_right_bumper,
            A_BTN : self._handle_a_btn,
            B_BTN : self._handle_unmapped,
            X_BTN : self._handle_unmapped,
            Y_BTN : self._handle_unmapped,
            DPAD_X: self._handle_unmapped,
            DPAD_Y: self._handle_unmapped,
            SELECT: self._handle_unmapped,
            START : self._handle_unmapped,
        }

    def _set_device(self, device_name):
        for path in list_devices():
            device = InputDevice(path)
            if device.name.upper() == device_name:
                self.device = device
                break
        else:
            message = "{} not found".format(device_name)
            raise Exception(message)

    def _normalize(self, value, min, max):
        value = value / max if value >= 0 else value / (-min)
        return value

    def _handle_left_joystick_x(self, value):
        pass

    def _handle_left_joystick_y(self, value):
        pass

    def _handle_left_trigger(self, value):
        value = self._normalize(value, min=0, max=TRIG_MAX)

    def _handle_left_bumper(self, value):
        """
        Adjust left motor bias.
        """
        pass

    def _handle_right_joystick_x(self, value):
        pass

    def _handle_right_joystick_y(self, value):
        pass

    def _handle_right_trigger(self, value):
        value = self._normalize(value, min=0, max=TRIG_MAX)

    def _handle_right_bumper(self, value):
        """
        Adjust right motor bias.
        """
        pass

    def _handle_a_btn(self, value):
        """
        Toggle forward and reverse.
        """
        pass

    def _handle_unmapped(self, value):
        print("No mapping for button ...")

    def _handle_event(self, event):
        if event.type in [ecodes.EV_KEY, ecodes.EV_ABS]:
            self.callbacks[event.code](event.value)

    def start(self):
        while True:
            for event in self.device.read_loop():
                self._handle_event(event)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-name", default=DEVICE_NAME)
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    controller = XboxOneSPad()
    controller.start()
