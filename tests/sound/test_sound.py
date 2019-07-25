import sys

sys.path.append("./devastator")

from robot import respeaker
from robot.helpers import get_data
from sound.emotion import Emotion
from sound.gunshot import Gunshot

if __name__ == "__main__":
    emotion_detector = Emotion()
    gunshot_detector = Gunshot()

    while True:
        samples = get_data(respeaker.HOST, respeaker.PORT)
        direction = respeaker.api.direction

        is_gunshot = gunshot_detector.detect(samples[:, 0])
        if is_gunshot:
            print("Gunshot(s)! Direction: {}".format(direction))

        emotion, confidence = emotion_detector.detect(samples[:, 0])
        if emotion:
            print("Emotion: {:10}\tConfidence: {:5.2}\tDirection: {:5}"
                    .format(emotion, confidence, direction))