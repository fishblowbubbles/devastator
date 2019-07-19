import argparse
import sys

sys.path.append("./devastator")

from robot import respeaker
from robot.helpers import get_data
from sound.helpers import emotion_detect, emotion_livestream

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen", action="store_true")
    args = parser.parse_args()

    if args.listen:
        emotion_livestream()
    else:
        samples = get_data(respeaker.HOST, respeaker.PORT)
        emotion_detect(samples[:, 0])
