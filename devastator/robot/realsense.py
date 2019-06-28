import argparse
import pickle
import socket
from multiprocessing import Process, Queue

import numpy as np
import pyrealsense2 as rs

HOST = "127.0.0.1"
PORT = 4444


def recv_frame(client):
    """
    Receives frame.
    """
    packets = []
    while True:
        packet = client.recv(1024)
        if not packet:
            break
        packets.append(packet)
    object = pickle.loads(b"".join(packets))
    return object


def get_frames(host=HOST, port=PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        rgbd = recv_frame(client)
    return rgbd


class D435i:
    def __init__(self, host, port):
        self.host, self.port = host, port
        self.requests = Queue()
        self.pipeline = rs.pipeline()
        self.pipeline.start()

    def _start_server(self):
        print("Starting server         ...")
        with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            while True:
                connection, _ = s.accept()
                self.requests.put(connection)

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

    def _process_requests(self, frames):
        while not self.requests.empty():
            conn = self.requests.get()
            rgbd = self._frames_to_rgbd(frames)
            self._send_and_shutdown(conn, rgbd)

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
    parser.add_argument("--port", default=PORT)
    args = parser.parse_args()

    d435i = D435i(host=args.host, port=int(args.port))
    d435i.run()
