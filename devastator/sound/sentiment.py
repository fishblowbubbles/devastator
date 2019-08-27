import scipy.io.wavfile as wavfile

from robot import respeaker
from robot.helpers import get_data
from sound.helpers import vokaturi_func

EMOTIONS = {None: "-", 0: "Neutral", 1: "Happy", 2: "Sad", 3: "Anger", 4: "Fear"}
THRESHOLD = 0.95


class Sentiment:
    def __init__(self, emotions=EMOTIONS):
        self.emotions = emotions

    def detect(self, samples, rate=respeaker.RATE):
        prediction, confidence = vokaturi_func(samples, rate)
        emotion = self.emotions[prediction]
        return emotion, confidence

    def listen(self, rate=respeaker.RATE,
               host=respeaker.HOST, port=respeaker.PORT):
        while True:
            samples = get_data(host, port)
            emotion, confidence = self.detect(samples[:, 0], rate)
            if emotion:
                direction = respeaker.api.direction
                print("Emotion: {:10}\tConfidence: {:5.2}\tDirection: {:5}"
                      .format(emotion, confidence, direction))
