import argparse
import os
import pickle
import socket
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame

from robot.helpers import connect_and_send
from robot import romeo

DEVICE_NAME = "Microsoft X-Box One S pad"

L_JS_X, L_JS_Y, L_TRIG = 0, 1, 2
R_JS_X, R_JS_Y, R_TRIG = 3, 4, 5
A_BTN, B_BTN = 0, 1
X_BTN, Y_BTN = 2, 3
DPAD = 0
L_BUMP, R_BUMP = 4, 5
SELECT, START = 6, 7

AXIS, HAT = pygame.JOYAXISMOTION, pygame.JOYHATMOTION
BTN_UP, BTN_DOWN = pygame.JOYBUTTONUP, pygame.JOYBUTTONDOWN

POLLING_RATE = 200
JS_THRESH = 0.1

UP, DOWN = 0, 1


class XPad:
    def __init__(self, device_name=DEVICE_NAME):
        pygame.init()
        self.device_name = device_name
        self.joystick = self._get_device()
        self.joystick.init()

    def _get_device(self):
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            if joystick.get_name() == self.device_name:
                return joystick
        else:
            message = "{} not found".format(self.device_name)
            raise Exception(message)

    def _get_events(self):
        events = {AXIS: {}, HAT: {}, BTN_DOWN: {}}
        for event in pygame.event.get():
            if event.type == AXIS:
                events[AXIS][event.axis] = event.value
            elif event.type == HAT:
                events[HAT][event.hat] = event.value
            elif event.type == BTN_DOWN:
                events[BTN_DOWN][event.button] = DOWN
        return events

    def run(self):
        while True:
            events = self._get_events()
            connect_and_send(events, romeo.HOST, romeo.PORT)
            time.sleep(1 / POLLING_RATE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-name", default=DEVICE_NAME)
    args = parser.parse_args()

    xpad = XPad(device_name=args.device_name)
    xpad.run()
