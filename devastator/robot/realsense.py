import argparse
import pickle
import socket
from multiprocessing import Process, Queue

import numpy as np
import pyrealsense2 as rs

from robot.helpers import recv_obj, send_data

HOST = "127.0.0.1"
PORT = 4444


class D435i:
    def __init__(self, host=HOST, port=PORT):
        self.host, self.port = host, port
        self.requests = Queue()
        self.pipeline = rs.pipeline()
        self.pipeline.start()

    def _frames_to_rgbd(self, frames):
        rgb, d = frames.get_color_frame(), frames.get_depth_frame()
        rgb, d = np.array(rgb.get_data()), np.array(d.get_data())
        d = d.reshape((720, 1280, 1))
        rgbd = np.concatenate((rgb, d), axis=2)
        return rgbd

<<<<<<< HEAD
    def _send_frames(self, connection, rgbd):
        try:
            connection.sendall(pickle.dumps(rgbd))
            connection.shutdown(socket.SHUT_RDWR)
        except ConnectionResetError:
            print("A connection was reset ...")
        except BrokenPipeError:
            print("A pipe broke ...")

    def _frames_to_rgbd(self, frames):
        rgb, d = frames.get_color_frame(), frames.get_depth_frame()
        rgb, d = np.array(rgb.get_data()), np.array(d.get_data())
        d = d.reshape((720, 1280, 1))
        rgbd = np.concatenate((rgb, d), axis=2)
        return rgbd

    def _send_and_shutdown(self, conn, rgbd):
        try:
            conn.sendall(pickle.dumps(rgbd))
            conn.shutdown(socket.SHUT_RDWR)
        except ConnectionResetError:
            print("A connection was reset  ...")
        except BrokenPipeError:
            print("A pipe broke            ...")

=======
>>>>>>> e0b4ada... respeaker integration
    def _process_requests(self, frames):
        rgbd = self._frames_to_rgbd(frames)
        while not self.requests.empty():
            connection = self.requests.get()
            send_data(connection, rgbd)

    def _start_server(self):
        with socket.socket() as server:
            server.bind((self.host, self.port))
            server.listen()
            while True:
                connection, _ = server.accept()
                self.requests.put(connection)

    def run(self):
        server = Process(target=self._start_server)
        server.start()
        try:
            while True:
                frames = self.pipeline.wait_for_frames()
                if self.requests.empty():
                    continue
                else:
                    self._process_requests(frames)
        finally:
            self.pipeline.stop()
            server.terminate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

<<<<<<< HEAD
    d435i = D435i(host=args.host, port=int(args.port))
=======
    d435i = D435i(host=args.host, port=args.port)
>>>>>>> develop
    d435i.run()
