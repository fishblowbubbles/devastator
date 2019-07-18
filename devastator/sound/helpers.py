import os
import time

import numpy as np
import scipy.io.wavfile as wavfile
from scipy import signal
from scipy.ndimage.filters import maximum_filter1d as max_filter

import robot.respeaker as respeaker
from sound.vokaturi import Vokaturi
from robot.helpers import get_data

EMOTIONS = {0: "Neutral", 1: "Happy", 2: "Sad", 3: "Anger", 4: "Fear"}

GUNSHOT_THRESHOLD = 1.0
_, GUNSHOT_TEMPLATE = wavfile.read("devastator/sound/data/normalized_template.wav")
INTERVAL = 1024


def rms_normalize(samples):
    samples = samples / max(samples)
    rms = (sum(samples ** 2) / len(samples)) ** 0.5
    samples = samples * rms
    return samples


def gunshot_detect(samples, template=GUNSHOT_TEMPLATE, threshold=GUNSHOT_THRESHOLD, interval=INTERVAL):
    samples = rms_normalize(samples)
    correlation = signal.correlate(samples, template, mode="same")
    correlation = max_filter(correlation, interval)
    correlation = np.amax(correlation)
    gunshot = correlation > threshold
    return gunshot


def gunshot_livestream():
    while True:
        samples = get_data(respeaker.HOST, respeaker.PORT)
        gunshot = gunshot_detect(samples)
        direction = respeaker.api.direction
        if gunshot:
            print("Gunshots: {}\tDirection: {:10}".format(gunshot, direction))
        else:
            print("No gunshot detected ...")


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
    detection = vokaturi_func(filename)
    return detection


def vokaturi_livestream(filename=".tmp/audio.wav", rate=respeaker.RATE):
    while True:
        samples = get_data(respeaker.HOST, respeaker.PORT)[:, 0]
        direction = respeaker.api.direction
        voice = respeaker.api.is_voice()
        if voice:
            emotion, confidence = vokaturi_detect(samples, rate, filename)
            print("Emotion: {:10}\tConfidence: {:10.2}\tDirection: {:10}"
                    .format(emotion, confidence, direction))
        else:
            print("No voice detected ...")
