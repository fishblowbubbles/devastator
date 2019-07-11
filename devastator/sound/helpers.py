import os

import scipy.io.wavfile as wavfile

from sound import Vokaturi


def normalize_data(data):
    data = data / max(data)
    rms = (sum(data ** 2) / len(data)) ** 0.5
    data = data * rms
    return data


def write_to_wav(self, samples, filename=".tmp/audio.wav"):
    wavfile.write(filename, self.rate, samples)


def vokaturi_func(filename):
    (rate, samples) = wavfile.read(filename)
    buffer_length = len(samples)
    c_buffer = Vokaturi.SampleArrayC(buffer_length)

    if samples.ndim == 1:
        c_buffer[:] = samples[:] / 32768.0
    else:
        c_buffer[:] = 0.5 * (samples[:, 0] + 0.0 + samples[:, 1]) / 32768.0

    voice = Vokaturi.Voice(rate, buffer_length)
    voice.fill(buffer_length, c_buffer)

    quality = Vokaturi.Quality()
    probabilities = Vokaturi.EmotionProbabilities()
    voice.extract(quality, probabilities)

    prediction = None
    if quality.valid:
        n = probabilities.neutrality
        h = probabilities.happiness
        s = probabilities.sadness
        a = probabilities.anger
        f = probabilities.fear
        prediction = max(n, h, s, a, f)

    return prediction
