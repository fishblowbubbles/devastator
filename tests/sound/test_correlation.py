import argparse
import sys

sys.path.append("./devastator")

import numpy as np

from robot import respeaker
from robot.helpers import get_data
from sound.helpers import calc_correlation

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-size", type=int, default=1024)
    args = parser.parse_args()

    samples = get_data(respeaker.HOST, respeaker.PORT)
    samples = np.transpose(samples)
