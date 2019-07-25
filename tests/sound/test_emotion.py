import argparse
import sys

sys.path.append("./devastator")

from robot import respeaker
from robot.helpers import get_data
from sound.emotion import Emotion

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen", action="store_true")
    args = parser.parse_args()

    emotion_detector = Emotion()
    if args.listen:
        emotion_detector.listen()
    else:
        samples = get_data(respeaker.HOST, respeaker.PORT)
        emotion, confidence =  emotion_detector.detect(samples[:, 0])
        print("Emotion: {:10}\tConfidence: {:5.2}"
              .format(emotion, confidence))