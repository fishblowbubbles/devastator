import numpy as np
import scipy.io.wavfile as wavfile

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

    prediction, confidence = "-", 0

    if quality.valid:
        n = probabilities.neutrality
        h = probabilities.happiness
        s = probabilities.sadness
        a = probabilities.anger
        f = probabilities.fear

        output = [n, h, s, a, f]
        prediction = np.argmax(output)
        confidence = output[prediction]

    return prediction, confidence
