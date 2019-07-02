import argparse
import pickle
import socket
from multiprocessing import Process, Queue
from threading import Thread
from time import sleep

import serial

from helpers import recv_obj

HOST = "192.168.1.228"
PORT = 8888

DEVICE_PATH = "/dev/serial/by-id/usb-Arduino_LLC_Arduino_Leonardo-if00"
BAUDRATE = 115200

L_JS_X, L_JS_Y, L_TRIG = 0, 1, 2
R_JS_X, R_JS_Y, R_TRIG = 3, 4, 5
DPAD_X, DPAD_Y = 16, 17
A_BTN, B_BTN = 304, 305
X_BTN, Y_BTN = 307, 308
L_BUMP, R_BUMP = 310, 311
SELECT, START = 314, 315

JS_MIN, JS_MAX = -32768, 32767
TRIG_MAX = 1023

L_MOTOR, R_MOTOR = 1, 2
L_POLARITY, R_POLARITY = -1, 1

## TODO
## add some ping functionality so if python crashes the bot will stop
## maybe use some special ASCII character?

## TODO
## fix the motor cutout at low PWM. use a HPF to bump the motor out of friction.
## implement this in the romeo.
## also i think the cutout pwm is a bit too low. maybe 11% is good?


def send_command(command, host=HOST, port=PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        try:
            client.connect((HOST, PORT))
            client.sendall(pickle.dumps(command))
            client.shutdown(socket.SHUT_RDWR)
        except ConnectionRefusedError:
            print("Connection refused      ...")


class Romeo:
    def __init__(self, host, port, device_path=DEVICE_PATH, baudrate=BAUDRATE, timeout=1):
        self.host, self.port = host, port
        self.device_path = device_path
        self.serial = serial.Serial(device_path, baudrate)
        self.timeout = timeout
        self.command_queue = Queue(maxsize=20)
        self.count = 0
        self.polarity = 1
        self._send("overshoot 4")
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
        self.state = {
            L_JS_Y: 0,
            L_TRIG: 0,
            R_JS_X: 0,
            R_TRIG: 0
        }
        self.enable()

    def _normalize_input(self, value, min, max):
        value = value / max if value >= 0 else value / (-min)
        return value

    def _handle_left_joystick_x(self, value):
        pass

    def _handle_left_joystick_y(self, value):
        value = self._normalize_input(value, min=JS_MIN, max=JS_MAX)
        self.state[L_JS_Y] = value


    def _handle_left_trigger(self, value):
        value = self._normalize_input(value, min=0, max=TRIG_MAX)
        # self.set_motor_speed(L_MOTOR, value * L_POLARITY)
        self.state[L_TRIG] = value

    def _handle_left_bumper(self, value):
        """
        Adjust left motor bias.
        """
        pass

    def _handle_right_joystick_x(self, value):
        value = self._normalize_input(value, min=JS_MIN, max=JS_MAX)
        self.state[R_JS_X] = value

    def _handle_right_joystick_y(self, value):
        pass

    def _handle_right_trigger(self, value):
        value = self._normalize_input(value, min=0, max=TRIG_MAX)
        # self.set_motor_speed(R_MOTOR, value * R_POLARITY)
        self.state[R_TRIG] = value

    def _handle_right_bumper(self, value):
        """
        Adjust right motor bias.
        """
        pass

    def _handle_a_btn(self, value):
        """
        Toggle forward and reverse.
        """
        if value == 1:
            if self.polarity == 1:
                self.polarity = -1
            elif self.polarity == -1:
                self.polarity = 1

    def _handle_unmapped(self, value):
        pass

    def set_direction(self, reverse_m1=False, reverse_m2=False):
        """
        A fix for the direction coz martin is lazy to swap the motor polarity.
        """
        pass

    def trim(self, motor, direction, volt_delta=0.05):
        """
        Trim the motor speeds so that a zero turning command will result in a nominally straight path for the robot.
        """
        pass

    def set_controller_verbosity(self, verbosity):
        """
        For debugging purposes, enables debug output over serial.
        """
        pass

    def set_overshoot(self, magnitude, length):
        """
        Sets the overshoot magnitude and length of the high shelf filter in the motor controller
        to tune the aggressiveness of the controller during a step change of motor power.
        """
        pass

    def set_motor_gamma(self, gamma):
        """
        Sets the nonlinearity of the motor response.

        PWM is calculated by the formula (in C language):
        s = m_speed == 0 ? 0 : (pow(abs(m_speed), motor_gamma)*(max_pwm_scale_1 - motor_cut_in_1) + motor_cut_in_1)
        """
        pass

    def set_timeout(self, millis=300):
        """
        NOT IMPLEMENTED IN ARDUINO CODE YET.
        Used to set the timeout for the watchdog timer in the arduino to stop running the motors in case python stops working.
        """
        pass

    def _send(self, msg):
        """
        Wraps the serial message in the correct format.
        """
        msg = "{}\n".format(msg).encode("utf-8")
        self.serial.write(msg)

    def enable(self):
        """
        Enables the motors.
        """
        self._send("enable")
        # self.buzz([1, 3])

    def disable(self):
        """
        Disables the motors and rejects any further commands.
        """
        self._send("disable")

    def test(self):
        """
        Runs a min-to-max motor speed sweep.
        """
        self._send("test")

    def lol(self, n_times=1):
        """
        Partay time.
        """
        self._send("lol " + str(n_times))

    def set_motor_speed(self, motor, speed):
        """
        Sets the motor speed.
        """
        if motor == L_MOTOR:
            speed *= L_POLARITY
        elif motor == R_MOTOR:
            speed *= R_POLARITY
        speed *= self.polarity
        s = "{} {:.3f}".format(int(motor), float(speed))
        self._send(s)

    def __call__(self, forward_speed, turn_speed):
        """
        Set the forward speed and turn speed.
        Positive forward_speed will drive the robot forward.
        Positive turn_speed is a left turn.
        Note that each command will be clipped to be between -1 and 1 in the romeo.
        """
        s1 = forward_speed - turn_speed
        s2 = forward_speed + turn_speed
        self.set_motor_speed(L_MOTOR, s1)
        self.set_motor_speed(R_MOTOR, s2)

    def _start_server(self):
        print("Starting server         ...")
        with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as server:
            server.bind((self.host, self.port))
            server.listen()
            while True:
                connection, _ = server.accept()
                code, value = recv_obj(connection)
                self.callbacks[code](value)
                # self.command_queue.put(command)

    def run(self):
        server = Thread(target=self._start_server)
        server.start()
        while True:
            # code, value = self.command_queue.get()
            try:
                self.serial.read_all()
                # self(self.state[L_JS_Y], self.state[R_JS_X])
                # self.callbacks[code](value)
                self.set_motor_speed(L_MOTOR, self.state[L_TRIG])
                self.set_motor_speed(R_MOTOR, self.state[R_TRIG])
            except KeyboardInterrupt:
                self.set_motor_speed(1, 0)
                self.set_motor_speed(2, 0)
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    romeo = Romeo(host=args.host, port=args.port)
    romeo.run()
