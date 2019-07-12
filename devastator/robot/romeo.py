import argparse
import itertools
import pickle
import socket
import sys

import serial

from robot import xpad
from robot.helpers import ConfigFile, recv_obj

CONFIG = ConfigFile("devastator/robot/config.ini")

HOST = "localhost"
# HOST = "192.168.1.178"  # UP-Squared 1
# HOST = "192.168.1.232"  # UP-Squared 2
PORT = 8888

DEVICE_ID = "usb-Arduino_LLC_Arduino_Leonardo-if00"
ENABLE, DISABLE = "enable", "disable"

L_MOTOR, R_MOTOR = 1, 2
L_POLARITY, R_POLARITY = -1, 1

CONTROL_MODES = ["Joystick", "Trigger"]


class Romeo:
    def __init__(self, device_id=DEVICE_ID, config=CONFIG, host=HOST, port=PORT):
        device_path = "/dev/serial/by-id/{}".format(device_id)
        self.serial = serial.Serial(device_path, config.get("romeo", "baudrate"))
        self.device_path, self.config = device_path, config
        self.host, self.port = host, port

        self.gamma = float(config.get("romeo", "gamma"))
        self.min_voltage = float(config.get("romeo", "minvoltage"))
        self.max_voltage = float(config.get("romeo", "maxvoltage"))
        self.set_overshoot(int(config.get("romeo", "overshoot")))
        self.set_voltage(L_MOTOR, float(config.get("romeo", "leftvoltage")))
        self.set_voltage(R_MOTOR, float(config.get("romeo", "rightvoltage")))
        self.enable_motors()

        self.change_direction = itertools.cycle([1, -1])
        self.change_control_mode = itertools.cycle(CONTROL_MODES)
        self.direction = next(self.change_direction)
        self.control_mode = next(self.change_control_mode)

        self.state = {xpad.L_JS_Y: 0,
                       xpad.L_TRIG: 0,
                       xpad.R_JS_X: 0,
                       xpad.R_TRIG: 0}

        self.callbacks = {xpad.AXIS: {xpad.L_JS_Y: self._handle_left_joystick_y,
                                      xpad.L_TRIG: self._handle_left_trigger,
                                      xpad.R_JS_X: self._handle_right_joystick_x,
                                      xpad.R_TRIG: self._handle_right_trigger},
                          xpad.HAT: {xpad.DPAD: self._handle_dpad},
                          xpad.BTN_DOWN: {xpad.A_BTN : self._handle_a_btn,
                                          xpad.B_BTN : self._handle_b_btn}}

    """ MATH HELPERS """

    def _gamma_func(self, value):
        sign = (-1, 1)[value >= 0]
        value = (abs(value) - xpad.JS_THRESH) / (1 - xpad.JS_THRESH)
        value = sign * (value ** self.gamma)
        return value

    def _normalize_js(self, value):
        if abs(value) <= xpad.JS_THRESH: return 0
        value = self._gamma_func(value)
        return value

    def _normalize_trig(self, value):
        value = (value + 1.0) / 2.0
        value = (0, value)[value > 0]
        return value

    """ INPUT CALLBACKS """

    def _handle_left_joystick_y(self, value):
        value = self._normalize_js(-value)
        self.state[xpad.L_JS_Y] = value

    def _handle_left_trigger(self, value):
        value = self._normalize_trig(value)
        self.state[xpad.L_TRIG] = value

    def _handle_right_joystick_x(self, value):
        value = self._normalize_js(-value)
        self.state[xpad.R_JS_X] = value

    def _handle_right_trigger(self, value):
        value = self._normalize_trig(value)
        self.state[xpad.R_TRIG] = value

    def _handle_dpad(self, value):
        x, y = value
        if x:
            self.trim_voltage(L_MOTOR, x)
            self.trim_voltage(R_MOTOR, -x)
        if y:
            self.trim_voltage(L_MOTOR, y)
            self.trim_voltage(R_MOTOR, y)

    def _handle_a_btn(self, value):
        if value == xpad.DOWN:
            if self.control_mode == "Trigger":
                self.direction = next(self.change_direction)
                print("Trigger Direction = {}".format(self.direction))

    def _handle_b_btn(self, value):
        if value == xpad.DOWN:
            self.control_mode = next(self.change_control_mode)
            print("Control Mode      = {}".format(self.control_mode))

    def _handle_events(self, events):
        for key, inputs in events.items():
            for event, value in inputs.items():
                try:
                    self.callbacks[key][event](value)
                except KeyError:
                    continue

    """ MOVEMENT CONTROLS """

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

    def _execute_movement(self):
        self.serial.read_all()
        if self.control_mode == "Joystick":
            self._js_movement()
        if self.control_mode == "Trigger":
            self._trig_movement()

    def set_motors(self, l_motor_speed, r_motor_speed):
        self.set_speed(L_MOTOR, l_motor_speed * L_POLARITY)
        self.set_speed(R_MOTOR, r_motor_speed * R_POLARITY)

    def stop_motors(self):
        self.set_motors(0, 0)

    """ SERIAL COMMANDS """

    def _send_serial(self, message):
        message = "{}\n".format(message).encode("utf-8")
        self.serial.write(message)

    def enable_motors(self):
        self._send_serial(ENABLE)
        self.serial.readline()

    def disable_motors(self):
        self._send_serial(DISABLE)
        self.serial.readline()

    def set_overshoot(self, magnitude):
        message = "overshoot {}".format(magnitude)
        self._send_serial(message)
        self.serial.readline()

    def set_speed(self, motor, speed):
        message = "{} {:.3f}".format(int(motor), float(speed))
        self._send_serial(message)

    def get_voltage(self, motor):
        message = "motor{}_voltage".format(motor)
        self._send_serial(message)
        voltage = self.serial.readline().decode("utf-8")
        voltage = float(voltage.rstrip().replace("\n", ""))
        return voltage

    def set_voltage(self, motor, voltage):
        self.config.save("romeo", "{}voltage".format(("left", "right")[motor - 1]), voltage)
        print("{} Motor Voltage   = {}".format(("L", "R")[motor - 1], voltage))
        message = "motor{}_voltage {}".format(motor, voltage)
        self._send_serial(message)

    def trim_voltage(self, motor, direction, voltage_delta=0.05):
        voltage = self.get_voltage(motor) + direction * voltage_delta
        voltage = (self.min_voltage, voltage)[voltage > self.min_voltage]
        voltage = (voltage, self.max_voltage)[voltage > self.max_voltage]
        self.set_voltage(motor, round(voltage, 2))

    """ MAIN LOOP """

    def run(self):
        with socket.socket() as server:
            server.bind((self.host, self.port))
            server.listen()
            try:
                while True:
                    connection, _ = server.accept()
                    events = recv_obj(connection)
                    self._handle_events(events)
                    self._execute_movement()
            finally:
                self.stop_motors()
