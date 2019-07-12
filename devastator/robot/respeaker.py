import argparse
import pickle
import socket
from collections import deque
from multiprocessing import Process, Queue

import numpy as np
import pyaudio
from scipy.io import wavfile

from robot.helpers import recv_obj, send_data

HOST = "127.0.0.1"
PORT = 5555

DEVICE_NAME = "ReSpeaker 4 Mic Array (UAC1.0)"

WIDTH = 2
CHUNK_SIZE = 1024
BUFFER_SIZE_IN_SECONDS = 5


class ReSpeaker:
    def __init__(self, width=WIDTH, chunk_size=CHUNK_SIZE, seconds=BUFFER_SIZE_IN_SECONDS,
                 device_name=DEVICE_NAME, host=HOST, port=PORT):
        self.host, self.port = host, port

        self.audio = pyaudio.PyAudio()
        self.device_info = self._get_device_info(device_name)
        self.stream = self._get_stream(self.device_info, width)

        num_samples = int(self.device_info["defaultSampleRate"] / chunk_size * seconds)
        self.channels, self.chunk_size = self.device_info["maxInputChannels"], chunk_size
        self.buffer = deque(maxlen=num_samples)
        self.requests = Queue()

    def _get_device_info(self, device_name):
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_name in device_info.get("name"):
                return device_info
        else:
            message = "{} not found".format(device_name)
            raise Exception(message)

    def _get_stream(self, device_info, width):
        format = self.audio.get_format_from_width(width)
        stream = self.audio.open(rate=int(device_info["defaultSampleRate"]),
                                 format=format,
                                 channels=device_info["maxInputChannels"],
                                 input=True,
                                 input_device_index=device_info["index"])
        return stream

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
        with socket.socket() as server:
            server.bind((self.host, self.port))
            server.listen()
            while True:
                connection, _ = server.accept()
                self.requests.put(connection)

    def get_sample(self):
        sample = self.stream.read(self.chunk_size, exception_on_overflow=False)
        sample = np.frombuffer(sample, dtype=np.int16)
        sample = sample[:, np.newaxis]
        return sample

    def run(self):
        server = Process(target=self._start_server)
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
