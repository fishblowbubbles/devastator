import argparse
import pickle
import socket
from collections import deque
from multiprocessing import Process, Queue

import numpy as np
import pyaudio
from scipy.io import wavfile

from robot.helpers import recv_obj, send_data
from robot.micarray import tuning

HOST = "localhost"
PORT = 7777

DEVICE_NAME = "ReSpeaker 4 Mic Array (UAC1.0)"

RATE, CHANNELS, WIDTH = 16000, 6, 2
CHUNK_SIZE = 1024
BUFFER_SIZE_IN_SECONDS = 20

api = tuning.find()


class ReSpeaker:
    def __init__(self, rate=RATE, channels=CHANNELS, width=WIDTH, chunk_size=CHUNK_SIZE,
                 seconds=BUFFER_SIZE_IN_SECONDS, device_name=DEVICE_NAME,
                 host=HOST, port=PORT):
        self.host, self.port = host, port
        self.audio = pyaudio.PyAudio()

        device_index = self._get_device_index(device_name)
        self.channels, self.chunk_size = channels, chunk_size
        self.stream = self.audio.open(rate=rate,
                                      format=self.audio.get_format_from_width(width),
                                      channels=channels,
                                      input=True,
                                      input_device_index=device_index)

        num_samples = int(rate / chunk_size * seconds)
        self.buffer = deque(maxlen=num_samples)
        self.requests = Queue()

    def _get_device_index(self, device_name):
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_name in device_info.get("name"):
                return i
        else:
            message = "{} not found".format(device_name)
            raise Exception(message)

    def _to_wav_array(self, samples, num_samples):
        shape =  (num_samples * self.chunk_size, self.channels)
        samples = np.reshape(samples, shape)
        return samples

    def _process_requests(self):
        samples = self._to_wav_array(self.buffer, len(self.buffer))
        while not self.requests.empty():
            connection = self.requests.get()
            send_data(connection, samples)

    def _start_server(self):
        server = socket.socket()
        server.bind((self.host, self.port))
        try:
            server.listen()
            while True:
                connection, _ = server.accept()
                self.requests.put(connection)
        finally:
            server.shutdown(socket.SHUT_RDWR)
            server.close()

    def get_sample(self):
        sample = self.stream.read(self.chunk_size, exception_on_overflow=False)
        sample = np.frombuffer(sample, dtype=np.int16)
        sample = sample[:, np.newaxis]
        return sample

    def run(self):
        server = Process(target=self._start_server)
        server.daemon = True
        server.start()
        try:
            while True:
                sample = self.get_sample()
                self.buffer.append(sample)
                if self.requests.empty():
                    continue
                else:
                    self._process_requests()
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            server.terminate()
