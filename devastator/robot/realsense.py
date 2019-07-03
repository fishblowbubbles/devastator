import argparse
import pickle
import socket
from multiprocessing import Process, Queue

import numpy as np
import pyrealsense2 as rs

from helpers import recv_obj

HOST = "127.0.0.1"
PORT = 4444


def get_frames(host=HOST, port=PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        rgbd = recv_obj(client)
    return rgbd


class D435i:
    def __init__(self, host=HOST, port=PORT):
        self.host, self.port = host, port
        self.requests = Queue()
        self.pipeline = rs.pipeline()
        self.pipeline.start()

    def _start_server(self):
        with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as server:
            server.bind((self.host, self.port))
            server.listen()
            while True:
                connection, _ = server.accept()
                self.requests.put(connection)

    def _frames_to_rgbd(self, frames):
        rgb, d = frames.get_color_frame(), frames.get_depth_frame()
        rgb, d = np.array(rgb.get_data()), np.array(d.get_data())
        d = d.reshape((720, 1280, 1))
        rgbd = np.concatenate((rgb, d), axis=2)
        return rgbd

    def _send_frames(self, connection, rgbd):
        try:
            connection.sendall(pickle.dumps(rgbd))
            connection.shutdown(socket.SHUT_RDWR)
        except ConnectionResetError:
            print("A connection was reset ...")
        except BrokenPipeError:
            print("A pipe broke ...")

    def _process_requests(self, frames):
        while not self.requests.empty():
            connection = self.requests.get()
            rgbd = self._frames_to_rgbd(frames)
            self._send_frames(connection, rgbd)

    def run(self):
        server = Process(target=self._start_server)
        server.start()
        try:
            while True:
                frames = self.pipeline.wait_for_frames()
                self._process_requests(frames)
        finally:
            self.pipeline.stop()
            server.terminate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    d435i = D435i(host=args.host, port=args.port)
    d435i.run()
