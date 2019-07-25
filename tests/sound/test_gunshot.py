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

    gunshot_detector = Gunshot()
    if args.listen:
        gunshot_detector.listen()
    else:
        if args.filename:
            _, samples = wavfile.read(args.filename)
            is_gunshot = gunshot_detector.detect(samples[:, 0])
        else:
            samples = get_data(respeaker.HOST, respeaker.PORT)
            is_gunshot = gunshot_detector.detect(samples[:, 0])
        print("Gunshot(s)?: {}".format(is_gunshot))
