import pickle
import socket
from multiprocessing import Process, Queue

import numpy as np
import pyrealsense2 as rs

from robot.helpers import recv_obj, send_data

HOST = "localhost"
PORT = 4444

RESOLUTION = (1280, 720)
FPS, FOV = 30, 87.0


class D435i():
    def __init__(self, host=HOST, port=PORT):
        self.host, self.port = host, port
        self.requests = Queue()

        self.align = rs.align(rs.stream.color)
        self.pipeline = rs.pipeline()
        self.pipeline.start()

    def _frames_to_rgbd(self, frames):
        rgb, d = frames.get_color_frame(), frames.get_depth_frame()
        rgb, d = np.array(rgb.get_data()), np.array(d.get_data())
        d = d.reshape((720, 1280, 1))
        rgbd = np.concatenate((rgb, d), axis=2)
        return rgbd

    def _process_requests(self, frames):
        rgbd = self._frames_to_rgbd(frames)
        while not self.requests.empty():
            connection = self.requests.get()
            send_data(connection, rgbd)

    def _start_server(self):
        with socket.socket() as server:
            server.bind((self.host, self.port))
            server.listen()
            try:
                while True:
                    connection, _ = server.accept()
                    self.requests.put(connection)
            finally:
                server.shutdown(socket.SHUT_RDWR)

    def run(self):
        server = Process(target=self._start_server)
        server.daemon = True
        server.start()
        try:
            while True:
                frames = self.pipeline.wait_for_frames()
                frames = self.align.process(frames)
                if not self.requests.empty():
                    self._process_requests(frames)
        finally:
            self.pipeline.stop()
            server.terminate()
