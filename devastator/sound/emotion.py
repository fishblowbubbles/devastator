import numpy as np
import scipy.io.wavfile as wavfile

from robot import respeaker
from robot.helpers import get_data
from sound.vokaturi import Vokaturi


def vokaturi_func(filename):
    rate, samples = wavfile.read(filename)
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

    emotion, confidence = "-", 0.0

    if quality.valid:
        n = probabilities.neutrality
        h = probabilities.happiness
        s = probabilities.sadness
        a = probabilities.anger
        f = probabilities.fear

        output = [n, h, s, a, f]
        prediction = np.argmax(output)
        emotion = Vokaturi.EMOTIONS[prediction]
        confidence = output[prediction]

    return emotion, confidence


class Emotion:
    def __init__(self, filename=".tmp/audio.wav"):
        self.filename = filename

    def detect(self, samples, rate=respeaker.RATE):
        wavfile.write(self.filename, rate, samples)
        emotion, confidence = vokaturi_func(self.filename)
        return emotion, confidence

    def listen(self, rate=respeaker.RATE,
               host=respeaker.HOST, port=respeaker.PORT):
        while True:
            samples = get_data(host, port)
            emotion, confidence = self.detect(samples[:, 0], rate)
            if emotion != "-":
                print("Emotion: {:10}\tConfidence: {:10.2}"
                      .format(emotion, confidence))
