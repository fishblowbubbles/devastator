import argparse
import sys

sys.path.append("./devastator")

import numpy as np
from scipy.io import wavfile

from robot import respeaker
from robot.helpers import get_data
from sound.helpers import gunshot_detect, gunshot_livestream

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen", action="store_true")
    parser.add_argument("--filename", default=None)
    args = parser.parse_args()

    if args.listen:
        gunshot_livestream()
    elif args.filename:
        _, samples = wavfile.read(args.filename)
        gunshot = gunshot_detect(samples[:, 0])
    else:
        samples = get_data(respeaker.HOST, respeaker.PORT)
        gunshot = gunshot_detect(samples[:, 0])
