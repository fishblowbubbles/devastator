import argparse
import pickle
import socket
from collections import deque
from multiprocessing import Process, Queue

import numpy as np
import pyaudio
from scipy.io import wavfile

from helpers import recv_obj, send_data

HOST = "127.0.0.1"
PORT = 5555

# DEVICE_NAME = "ReSpeaker 4 Mic Array (UAC1.0)"
DEVICE_NAME = "HDA Intel PCH: ALC233 Analog (hw:0,0)"

# RATE=16000
RATE = 44100
# CHANNELS = 6
CHANNELS = 1
WIDTH = 2

CHUNK_SIZE = 1024
SECONDS = 5


class ReSpeaker:
    def __init__(self, rate=RATE, width=WIDTH, channels=CHANNELS, chunk_size=CHUNK_SIZE, seconds=SECONDS,
                 device_name=DEVICE_NAME, host=HOST, port=PORT):
        self.host, self.port = host, port

        self.audio = pyaudio.PyAudio()
        self.rate, self.channels, self.chunk_size = rate, channels, chunk_size
        self.stream = self._get_stream(device_name, rate, width, channels)

        num_samples = int(self.rate / self.chunk_size * seconds)
        self.buffer = deque(maxlen=num_samples)
        self.requests = Queue()

    def _get_stream(self, device_name, rate, width, channels):
        device_index = self._get_device_index(device_name)
        format = self.audio.get_format_from_width(width)
        stream = self.audio.open(rate=rate,
                                 format=format,
                                 channels=channels,
                                 input=True,
                                 input_device_index=device_index)
        return stream

    def _get_device_index(self, device_name):
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info.get("name") == device_name:
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
        with socket.socket() as server:
            server.bind(self.host, self.port)
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=SECONDS)
    args = parser.parse_args()

    respeaker = ReSpeaker()
    respeaker.run()
