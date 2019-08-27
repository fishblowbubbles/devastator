import sys

sys.path.append("./devastator")

from robot import respeaker
from robot.helpers import get_data
from sound.sentiment import Sentiment
from sound.gunshot import Gunshot

if __name__ == "__main__":
    sentiment = Sentiment()
    gunshot = Gunshot()

    while True:
        samples = get_data(respeaker.HOST, respeaker.PORT)
        direction = respeaker.api.direction

        is_gunshot = gunshot.detect(samples[:, 0])
        if is_gunshot:
            print("Gunshot(s)! Direction: {}".format(direction))

        emotion, confidence = sentiment.detect(samples[:, 0])
        if emotion != "-":
            print("Emotion: {:10}\tConfidence: {:5.2}\tDirection: {}"
                    .format(emotion, float(confidence), direction))
