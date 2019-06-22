import argparse
import sys

sys.path.append(".")

import cv2
import numpy as np

import devastator.robot.realsense as realsense
import devastator.vision.darknet as darknet
from devastator.vision.helpers import load_names, load_colors
from devastator.helpers import predict, livestream

WEIGHTS = "devastator/vision/darknet/backup/custom_8.weights"
NAMES = "devastator/vision/darknet/data/custom_8.names"
DATA = "devastator/vision/darknet/cfg/custom_8.data"
CFG = "devastator/vision/darknet/cfg/custom_8.cfg"

FPS = 24
THRESH = 0.1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--fps", type=int, default=FPS)
    parser.add_argument("--thresh", type=float, default=THRESH)
    args = parser.parse_args()

    names = load_names(path=NAMES)
    colors = load_colors(n_classes=len(names))

    net = darknet.load_net(CFG.encode("ascii"), WEIGHTS.encode("ascii"), 0)
    meta = darknet.load_meta(DATA.encode("ascii"))

    if args.video:
        livestream(net, meta, names, colors, thresh=args.thresh, fps=args.fps)
    else:
        predict(net, meta, names, colors, thresh=args.thresh)
        cv2.waitKey(0)
