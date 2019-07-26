import argparse
import sys

sys.path.append("./devastator")

from robot import respeaker
from robot.helpers import get_data
from sound.sentiment import Sentiment

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen", action="store_true")
    args = parser.parse_args()

    sentiment = Sentiment()
    if args.listen:
        sentiment.listen()
    else:
        samples = get_data(respeaker.HOST, respeaker.PORT)
        emotion, confidence = sentiment.detect(samples[:, 0])
        print("Emotion: {:10}\tConfidence: {:5.2}"
              .format(emotion, confidence))