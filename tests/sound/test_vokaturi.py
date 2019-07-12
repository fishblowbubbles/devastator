import argparse
import sys

sys.path.append("./devastator")

from robot import respeaker
from helpers import vokaturi_livestream
from sound.helpers import vokaturi_detect
from robot.helpers import get_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen", action="store_true")
    parser.add_argument("--interval", type=float, default=0.5)
    args = parser.parse_args()

    if args.listen:
        vokaturi_livestream(interval=args.interval)
    else:
        samples = get_data(respeaker.HOST, respeaker.PORT)
        vokaturi_detect(samples)