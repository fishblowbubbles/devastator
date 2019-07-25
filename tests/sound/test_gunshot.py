import argparse
import sys

sys.path.append("./devastator")

import numpy as np
from scipy.io import wavfile

from robot import respeaker
from robot.helpers import get_data
from sound.gunshot import Gunshot

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen", action="store_true")
    parser.add_argument("--filename")
    args = parser.parse_args()

    gunshot = Gunshot()
    if args.listen:
        gunshot.listen()
    elif args.filename:
        _, samples = wavfile.read(args.filename)
        is_gunshot = gunshot.detect(samples[:, 0])
    else:
        samples = get_data(respeaker.HOST, respeaker.PORT)
        is_gunshot = gunshot.detect(samples[:, 0])
