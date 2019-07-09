import os

import scipy.io.wavfile
import speech_recognition as sr

import Vokaturi


def write_to_wav(audio, filename):
    with open(filename, "wb") as file:
        file.write(audio.get_wav_data())


def vokaturi_func(filename):
    (sample_rate, samples) = scipy.io.wavfile.read(filename)
    c_buffer = Vokaturi.SampleArrayC(len(samples))

    if samples.ndim == 1:
        c_buffer[:] = samples[:] / 32768.0
    else:
        c_buffer[:] = 0.5 * (samples[:, 0] + 0.0 + samples[:, 1]) / 32768.0

    voice = Vokaturi.Voice(sample_rate, buffer_length)
    voice.fill(buffer_length, c_buffer)

    quality = Vokaturi.Quality()
    probabilities = Vokaturi.EmotionProbabilities()
    voice.extract(quality, probabilities)

    if quality.valid:
        n = probabilities.neutrality
        h = probabilities.happiness
        s = probabilities.sadness
        a = probabilities.anger
        f = probabilities.fear
        prediction = max(n, h, s, a, f)
    else:
        print("No voice detected ...")

    voice.destroy()


def listening_func(recognizer, source, filename="tmp/audio.wav", duration=5):
    audio = recognizer.record(source, duration=duration)
    write_to_wav(audio, filename)
    vokaturi_func(filename)
