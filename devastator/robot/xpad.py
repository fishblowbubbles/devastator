import argparse
import os
import pickle
import socket
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame

from robot.helpers import connect_and_send

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
    def __init__(self, target_host, target_port, device_name=DEVICE_NAME):
        pygame.init()
        self.device_name = device_name
        self.target_host, self.target_port = target_host, target_port
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

    def _process_inputs(self, events):
        inputs = {AXIS: {}, HAT: {}, BTN_DOWN: {}}
        for event in events:
            if event.type == AXIS:
                inputs[AXIS][event.axis] = event.value
            elif event.type == HAT:
                inputs[HAT][event.hat] = event.value
            elif event.type == BTN_DOWN:
                inputs[BTN_DOWN][event.button] = DOWN
        return inputs

    def _get_inputs(self):
        events = pygame.event.get()
        if not events: return None
        inputs = self._process_inputs(events)
        return inputs

    def run(self):
        while True:
            inputs = self._get_inputs()
            if inputs: connect_and_send(inputs, self.target_host, self.target_port)
            time.sleep(1 / POLLING_RATE)
