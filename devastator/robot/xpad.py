import argparse
import os
import pickle
import socket
import time
from copy import deepcopy

import pygame

from robot.helpers import connect_and_send
from robot import romeo

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

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
UP, DOWN = 0, 1

POLLING_RATE = 200
JS_THRESH = 0.1

STATE = {AXIS: {}, HAT: {}, BTN_DOWN: {}}


class XPad:
    def __init__(self, target_host, target_port, device_name=DEVICE_NAME):
        pygame.init()

        self.device_name = device_name
        self.target_host, self.target_port = target_host, target_port
        self.joystick = self._get_device()
        self.joystick.init()

        self.callbacks = {
            AXIS: self._handle_axis,        # joystick and triggers
            HAT: self._handle_hat,          # d-pad
            BTN_DOWN: self._handle_btn_down
        }

    def _get_device(self):
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            if joystick.get_name() == self.device_name:
                return joystick
        else:
            message = "{} not found".format(self.device_name)
            raise Exception(message)

    def _handle_axis(self, event):
        self.state[AXIS][event.axis] = event.value

    def _handle_hat(self, event):
        self.state[HAT][event.hat] = event.value

    def _handle_btn_down(self, event):
        self.state[BTN_DOWN][event.button] = DOWN

    def _set_state(self, events):
        for event in events:
            try:
                self.callbacks[event.type](event)
            except KeyError:
                continue

    def _send_inputs(self):
        events = pygame.event.get()
        if events:
            self.state = deepcopy(STATE)
            self._set_state(events)
            connect_and_send(self.state,
                             self.target_host,
                             self.target_port)
            self.state = None

    def run(self):
        while True:
            self._send_inputs()
