import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage.filters import maximum_filter1d as max_filter

from robot import respeaker
from robot.helpers import get_data

THRESHOLD = 0.5
_, TEMPLATE = wavfile.read("devastator/sound/data/normalized_template.wav")
LENGTH, INTERVAL = 163840, 2000


class Gunshot:
    def __init__(self, template=TEMPLATE, length=LENGTH, interval=INTERVAL):
        self.template = template
        self.length = length
        self.interval = interval

    def _rms(self, data):
        output = (sum(data**2) / len(data))**0.5
        return output

    def _normalize(self, data):
        # output = data / max(data)             # 32767
        # output = output * self.rms(output)    # 0.0707665
        output = data / 60000 * 0.0707665
        return output

    def detect(self, samples, threshold=THRESHOLD):
        samples = self._normalize(samples[:self.length])
        correlation = signal.correlate(samples, self.template, mode="same")
        correlation = max_filter(correlation, self.interval)
        correlation = np.amax(correlation)
        is_gunshot = correlation > threshold
        return is_gunshot

    def listen(self, host=respeaker.HOST, port=respeaker.PORT):
        while True:
            samples = get_data(host, port)
            is_gunshot = self.detect(samples[:, 0])
            if is_gunshot:
                direction = respeaker.api.direction
                print("Gunshot(s)! Direction: {}"
                      .format(direction))
