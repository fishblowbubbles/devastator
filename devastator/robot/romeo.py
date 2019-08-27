import itertools
import socket

import serial
import numpy as np
from threading import Thread

from robot import xpad
from robot.helpers import ConfigFile, recv_obj, connect_and_send

CONFIG = ConfigFile("devastator/robot/config.ini")

# HOST = "192.168.1.178"  # UP-Squared 1
HOST = "192.168.1.232"  # UP-Squared 2
# HOST = "localhost"
PORT = 6060

AUTO_HOST = "localhost"
AUTO_PORT = 7777 

DEVICE_ID = "usb-Arduino_LLC_Arduino_Leonardo-if00"
ENABLE, DISABLE = "enable", "disable"

L_MOTOR, R_MOTOR = 1, 2
L_POLARITY, R_POLARITY = -1, 1

CONTROL_MODES = ["Joystick", "Trigger"]
# NAVIGATION_MODES = ["manual", "auto"]


class Romeo:
    def __init__(self, device_id=DEVICE_ID, config=CONFIG, 
                 xpad_host=HOST, xpad_port=PORT,
                 auto_host=AUTO_HOST, auto_port=AUTO_PORT,
                 ctrl_host="localhost", ctrl_port=5678):
        device_path = "/dev/serial/by-id/{}".format(device_id)
        self.serial = serial.Serial(device_path,
                                    config.get("romeo", "baudrate"))
        self.device_path, self.config = device_path, config

        self.xpad_host, self.xpad_port = xpad_host, xpad_port
        self.auto_host, self.auto_port = auto_host, auto_port
        self.ctrl_host, self.ctrl_port = ctrl_host, ctrl_port

        self.gamma = float(config.get("romeo", "gamma"))
        self.min_voltage = float(config.get("romeo", "minvoltage"))
        self.max_voltage = float(config.get("romeo", "maxvoltage"))
        self.set_overshoot(float(config.get("romeo", "overshoot")))
        self.set_voltage(L_MOTOR, float(config.get("romeo", "leftvoltage")))
        self.set_voltage(R_MOTOR, float(config.get("romeo", "rightvoltage")))
        self.enable_motors()

        self.change_direction = itertools.cycle([1, -1])
        self.change_control_mode = itertools.cycle(CONTROL_MODES)
        # self.change_navigation_mode = itertools.cycle(NAVIGATION_MODES)
        
        self.direction = next(self.change_direction)
        self.control_mode = next(self.change_control_mode)
        self.navigation_mode = "auto"

        self.state = {
            xpad.L_JS_Y: 0,
            xpad.L_TRIG: 0,
            xpad.R_JS_X: 0,
            xpad.R_TRIG: 0
        }

        self.callbacks = {
            xpad.AXIS: {
                xpad.L_JS_Y: self._handle_left_joystick_y,  # throttle
                xpad.L_TRIG: self._handle_left_trigger,     # left motor
                xpad.R_JS_X: self._handle_right_joystick_x, # steering
                xpad.R_TRIG: self._handle_right_trigger     # right motor
            },
            xpad.HAT: {
                xpad.DPAD: self._handle_dpad                # adjust/trim motor voltage
            },
            xpad.BTN_DOWN: {
                xpad.A_BTN: self._handle_a_btn,             # toggle direction (trigger mode only)
                xpad.B_BTN: self._handle_b_btn,             # toggle control mode
                xpad.X_BTN: self._handle_x_btn,
                xpad.Y_BTN: self._handle_y_btn
            }
        }

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

    def _handle_x_btn(self, value):
        if value == xpad.DOWN:
            self.navigation_mode = "manual"
            print("Navigation Mode   = {}".format(self.navigation_mode))

    def _handle_y_btn(self, value):
        if value == xpad.DOWN:
            self.navigation_mode = "auto"
            print("Navigation Mode   = {}".format(self.navigation_mode))

    def _handle_events(self, events):
        for key, inputs in events.items():
            for event, value in inputs.items():
                try:
                    self.callbacks[key][event](value)
                except KeyError:
                    continue

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

    """ MOVEMENT CONTROLS """

    def _js_movement(self):
        forward_speed = self.state[xpad.L_JS_Y]
        turn_speed = self.state[xpad.R_JS_X]
        l_motor_speed = np.clip(forward_speed - turn_speed, -1, 1)
        r_motor_speed = np.clip(forward_speed + turn_speed, -1, 1)
        self.set_motors(l_motor_speed, r_motor_speed)

    def _trig_movement(self):
        l_motor_speed = np.clip(self.state[xpad.L_TRIG] * self.direction, -1, 1)
        r_motor_speed = np.clip(self.state[xpad.R_TRIG] * self.direction, -1, 1)
        print(l_motor_speed, r_motor_speed)
        self.set_motors(l_motor_speed, r_motor_speed)

    def _execute_manual_movement(self):
        self.serial.read_all()
        if self.control_mode == "Joystick":
            self._js_movement()
        if self.control_mode == "Trigger":
            self._trig_movement()

    def _execute_auto_movement(self, data):
        """
        self.serial.read_all()
        l_motor_speed = data["u_out"][0, 0] * L_POLARITY
        r_motor_speed = data["u_out"][1, 0] * R_POLARITY   
        self.set_speed(L_MOTOR, l_motor_speed)
        self.set_speed(R_MOTOR, r_motor_speed)
        data = {"mode": self.navigation_mode}
        connect_and_send(data, self.ctrl_host, self.ctrl_port)
        print("L: {}, R: {}".format(l_motor_speed, r_motor_speed))
        """
        self.serial.read_all()
        if self.control_mode == "Joystick":
            self._js_movement()
        if self.control_mode == "Trigger":
            self._trig_movement()

    def set_motors(self, l_motor_speed, r_motor_speed):
        data = {"u_man": np.array([[l_motor_speed], [r_motor_speed]]), 
                "mode": self.navigation_mode}
        connect_and_send(data, self.ctrl_host, self.ctrl_port)
        self.set_speed(L_MOTOR, l_motor_speed * L_POLARITY)
        self.set_speed(R_MOTOR, r_motor_speed * R_POLARITY)
        
    def stop_motors(self):
        self.set_motors(0, 0)

    """ MAIN LOOP """

    def _start_server(self):
        with socket.socket() as server:
            server.bind((self.xpad_host, self.xpad_port))
            server.listen()
            while True:
                connection, _ = server.accept()
                events = recv_obj(connection)
                self._handle_events(events)
                if self.navigation_mode == "manual":
                    self._execute_manual_movement()

    def run(self):
        xpad_server = Thread(target=self._start_server)
        xpad_server.daemon = True
        xpad_server.start()
        with socket.socket() as auto_server:
            try:
                auto_server.bind((self.auto_host, self.auto_port))
                auto_server.listen()
                while True:
                    connection, _ = auto_server.accept()
                    data = recv_obj(connection)
                    self._handle_events(data)
                    if self.navigation_mode == "auto":
                        self._execute_auto_movement(data)
            finally:
                auto_server.shutdown(socket.SHUT_RDWR)
                auto_server.close()
                xpad_server._stop()
                self.stop_motors()
