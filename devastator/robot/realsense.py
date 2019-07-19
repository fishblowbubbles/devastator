import pickle
import socket
from multiprocessing import Process, Queue

import numpy as np
import pyrealsense2 as rs

HOST = "127.0.0.1"
PORT = 4444


class D435i():
    def __init__(self, host, port):
        self.host, self.port = host, port
        self.requests = Queue()
        self.pipeline = rs.pipeline()
        self.pipeline.start()
        align_to = rs.stream.color
        self.align = rs.align(align_to)


    def start_server(self):
        print("Starting server         ...")
        with socket.socket(family=socket.AF_INET,
                           type=socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            while True:
                connection, _ = s.accept()
                self.requests.put(connection)

    def process_requests(self, frames):
        while not self.requests.empty():
            connection = self.requests.get()
            rgb, d = frames.get_color_frame(), frames.get_depth_frame()
            rgb, d = np.array(rgb.get_data()), np.array(d.get_data())
            d = d.reshape((720, 1280, 1))
            rgbd = np.concatenate((rgb, d), axis=2)
            try:
                connection.sendall(pickle.dumps(rgbd))
                connection.shutdown(socket.SHUT_RDWR)
            except ConnectionResetError:
                print("A connection was reset  ...")
            except BrokenPipeError:
                print("A pipe broke            ...")

    def run(self):
        server = Process(target=self.start_server)
        server.start()
        try:
            while True:
                frames = self.pipeline.wait_for_frames()
                aligned_frames = self.align.process(frames)
                self.process_requests(aligned_frames)
        finally:
            self.pipeline.stop()
            server.terminate()


if __name__ == "__main__":
    d435i = D435i(host=HOST, port=PORT)
    d435i.run()
