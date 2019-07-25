import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage.filters import maximum_filter1d as max_filter

from robot import respeaker
from robot.helpers import get_data

THRESHOLD = 0.05
_, TEMPLATE = wavfile.read("devastator/sound/data/normalized_template.wav")
LENGTH, INTERVAL = 163840, 2000


def rms(data):
    output = (sum(data**2) / len(data))**0.5
    return output


def normalize(data):
    output = data / max(data)
    output = output * rms(output)
    return output


class Gunshot:
    def __init__(self, template=TEMPLATE, threshold=THRESHOLD,
                 length=LENGTH, interval=INTERVAL):
        self.template, self.threshold = template, threshold
        self.length, self.interval = length, interval

    def detect(self, samples):
        samples = normalize(samples[:self.length])
        correlation = signal.correlate(samples, self.template, mode="same")
        correlation = max_filter(correlation, self.interval)
        correlation = np.amax(correlation)
        is_gunshot = correlation > self.threshold
        return is_gunshot

    def listen(self, host=respeaker.HOST, port=respeaker.PORT):
        while True:
            samples = get_data(host, port)
            is_gunshot = self.detect(samples[:, 0])
            if is_gunshot:
                print("Gunshot(s)? {}".format(is_gunshot))
