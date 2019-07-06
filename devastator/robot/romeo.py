import argparse
import itertools
import pickle
import socket
import sys
from threading import Thread

import serial

import xpad as xpad
from helpers import recv_obj

# HOST = "192.168.1.178"  # UP-Squared 1
HOST = "192.168.1.232"  # UP-Squared 2
PORT = 8888

DEVICE_ID = "usb-Arduino_LLC_Arduino_Leonardo-if00"
BAUDRATE = 115200

ENABLE, DISABLE, TEST = "enable", "disable", "test"
OVERSHOOT, TIMEOUT, TRIM = "overshoot", "timeout", "trim"
GAMMA = 0.5

L_MOTOR, R_MOTOR = 1, 2
L_POLARITY, R_POLARITY = -1, 1

JS, TRIG = 0, 1


def send_command(command, host=HOST, port=PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        try:
            client.connect((HOST, PORT))
            client.sendall(pickle.dumps(command))
            client.shutdown(socket.SHUT_RDWR)
        except ConnectionRefusedError:
            print("The connection was refused ...")


class Romeo:
    def __init__(self, host=HOST, port=PORT):
        device_path = "/dev/serial/by-id/{}".format(DEVICE_ID)
        self.serial = serial.Serial(device_path, BAUDRATE)
        self.host, self.port = host, port
        self.device_path = device_path
        self.enable_motors()

        self.change_direction = itertools.cycle([1, -1])
        self.change_control_mode = itertools.cycle([JS, TRIG])
        self.toggle_left_trim = itertools.cycle([False, True])
        self.toggle_right_trim = itertools.cycle([False, True])

        self.direction = next(self.change_direction)
        self.control_mode = next(self.change_control_mode)
        self.left_trim = next(self.toggle_left_trim)
        self.right_trim = next(self.toggle_right_trim)

        self.state = {
            xpad.L_JS_Y: 0,
            xpad.L_TRIG: 0,
            xpad.R_JS_X: 0,
            xpad.R_TRIG: 0
        }
        self.callbacks = {
            xpad.L_JS_Y: self._handle_left_joystick_y,   # forward-backward movement
            xpad.L_TRIG: self._handle_left_trigger,      # left motor power
            xpad.L_BUMP: self._handle_left_bumper,       # toggle left motor trimming
            xpad.R_JS_X: self._handle_right_joystick_x,  # left-right movement
            xpad.R_TRIG: self._handle_right_trigger,     # right motor power
            xpad.R_BUMP: self._handle_right_bumper,      # toggle right motor trimming
            xpad.DPAD_Y: self._handle_dpad_y,            # up-down motor trimming
            xpad.A_BTN : self._handle_a_btn,             # change direction
            xpad.B_BTN : self._handle_b_btn,             # change control mode
            xpad.L_JS_X: self._handle_unmapped,
            xpad.R_JS_Y: self._handle_unmapped,
            xpad.X_BTN : self._handle_unmapped,
            xpad.Y_BTN : self._handle_unmapped,
            xpad.DPAD_X: self._handle_unmapped,
            xpad.SELECT: self._handle_unmapped,
            xpad.START : self._handle_unmapped,
        }

    def _normalize_js(self, value):
        value = ((value / xpad.JS_MAX) - xpad.JS_THRESH
                 if value >= 0
                 else (value / (-xpad.JS_MIN) + xpad.JS_THRESH))
        value = (math.pow(value / (1 - xpad.JS_THRESH), GAMMA)
                 if abs(value) > xpad.JS_THRESH
                 else 0)
        return value

    def _normalize_trig(self, value):
        value = value / xpad.TRIG_MAX
        return value

    def _handle_left_joystick_y(self, value):
        value = self._normalize_js(value)
        self.state[xpad.L_JS_Y] = -value

    def _handle_left_trigger(self, value):
        value = self._normalize_trig(value)
        self.state[xpad.L_TRIG] = value

    def _handle_left_bumper(self, value):
        if value == xpad.BTN_DOWN:
            self.left_trim = next(self.toggle_left_trim)

    def _handle_right_joystick_x(self, value):
        value = self._normalize_js(value)
        self.state[xpad.R_JS_X] = value

    def _handle_right_trigger(self, value):
        value = self._normalize_trig(value)
        self.state[xpad.R_TRIG] = value

    def _handle_right_bumper(self, value):
        if value == xpad.BTN_DOWN:
            self.right_trim = next(self.toggle_right_trim)

    def _handle_dpad_y(self, value):
        if value == xpad.DPAD_UP or value == xpad.DPAD_DOWN:
            if self.left_trim:
                self._trim_voltage(L_MOTOR, value)
            if self.right_trim:
                self._trim_voltage(R_MOTOR, value)

    def _handle_a_btn(self, value):
        if value == xpad.BTN_DOWN:
            self.direction = next(self.change_direction)

    def _handle_b_btn(self, value):
        if value == xpad.BTN_DOWN:
            self.control_mode = next(self.change_control_mode)

    def _handle_unmapped(self, value):
        pass

    def _start_server(self):
        with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as server:
            server.bind((self.host, self.port))
            server.listen()
            while True:
                connection, _ = server.accept()
                code, value = recv_obj(connection)
                self.callbacks[code](value)

    def _js_movement(self):
        forward_speed = self.state[xpad.L_JS_Y]
        turn_speed = self.state[xpad.R_JS_X]
        l_motor_speed = forward_speed - turn_speed
        r_motor_speed = forward_speed + turn_speed
        self.set_motors(l_motor_speed, r_motor_speed)

    def _trig_movement(self):
        l_motor_speed = self.state[xpad.L_TRIG] * self.direction
        r_motor_speed = self.state[xpad.R_TRIG] * self.direction
        self.set_motors(l_motor_speed, r_motor_speed)

    def _send_serial(self, message):
        message = "{}\n".format(message).encode("utf-8")
        self.serial.write(message)

    def _set_overshoot(self, magnitude, length):
        # message = "{} {} {}".format(OVERSHOOT, magnitude, length)
        # self._send_serial(message)
        pass

    def _set_timeout(self, millis=300):
        # message = "{} {}".format(TIMEOUT, millis)
        # self._send_serial(message)
        pass

    def _trim_voltage(self, motor, direction, voltage_delta=0.05):
        # message = "{} {} {}".format(motor, direction, voltage_delta)
        # self._send_serial(message)
        pass

    def enable_motors(self):
        self._send_serial(ENABLE)

    def disable_motors(self):
        self._send_serial(DISABLE)

    def test_motors(self):
        self._send_serial(TEST)

    def set_speed(self, motor, speed):
        message = "{} {:.3f}".format(int(motor), float(speed))
        self._send_serial(message)

    def set_motors(self, l_motor_speed, r_motor_speed):
        self.set_speed(L_MOTOR, l_motor_speed * L_POLARITY)
        self.set_speed(R_MOTOR, r_motor_speed * R_POLARITY)

    def stop_motors(self):
        self.set_motors(0, 0)

    def run(self):
        server = Thread(target=self._start_server)
        server.daemon = True
        server.start()
        try:
            while True:
                self.serial.read_all()
                if self.control_mode == JS:
                    self._js_movement()
                if self.control_mode == TRIG:
                    self._trig_movement()
        finally:
            self.stop_motors()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    romeo = Romeo(host=args.host, port=args.port)
    romeo.run()
