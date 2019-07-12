import os

import numpy as np
import scipy.io.wavfile as wavfile
from scipy import signal
from scipy.ndimage.filters import maximum_filter1d as max_filter

import robot.respeaker as respeaker
from sound.vokaturi import Vokaturi

EMOTIONS = {0: "Neutral", 1: "Happy", 2: "Sad", 3: "Anger", 4: "Fear"}
_, TEMPLATE = wavfile.read("devastator/sound/data/normalized_template.wav")


def rms_normalize(samples):
    samples = samples / max(samples)
    rms = (sum(samples ** 2) / len(samples)) ** 0.5
    samples = samples * rms
    return samples


def calc_correlation(samples, template=TEMPLATE):
    samples = rms_normalize(samples)
    correlation = signal.correlate(samples, template, mode="same")
    correlation = max_filter(correlation, 2000)
    correlation = np.amax(correlation) > 0.5
    return correlation


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
        emotion = EMOTIONS[prediction]
        confidence = output[prediction]

    return emotion, confidence


def vokaturi_detect(samples, rate=respeaker.RATE, filename=".tmp/audio.wav"):
    wavfile.write(filename, rate, samples)
    emotion, confidence = vokaturi_func(filename)
    print("Emotion: {:10}\tConfidence: {:10.2}".format(emotion, confidence))
