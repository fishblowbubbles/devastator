import argparse
import sys

sys.path.append("./devastator")

import cv2
import numpy as np

import robot.realsense as realsense
import vision.darknet as darknet
from helpers import darknet_livestream
from robot.helpers import get_data
from vision.helpers import Annotator, darknet_detect

PATH2WEIGHTS = "devastator/vision/darknet/backup/custom_8.weights"
PATH2NAMES = "devastator/vision/darknet/data/custom_8.names"
PATH2DATA = "devastator/vision/darknet/cfg/custom_8.data"
PATH2CFG = "devastator/vision/darknet/cfg/custom_8.cfg"

FPS = 24
THRESH = 0.1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--fps", type=int, default=FPS)
    parser.add_argument("--thresh", type=float, default=THRESH)
    args = parser.parse_args()

    net = darknet.load_net(PATH2CFG.encode("ascii"), PATH2WEIGHTS.encode("ascii"), 0)
    meta = darknet.load_meta(PATH2DATA.encode("ascii"))
    annotator = Annotator(path2names=PATH2NAMES)

    if args.video:
        darknet_livestream(net, meta, annotator, thresh=args.thresh, fps=args.fps)
    else:
        rgbd = get_data(realsense.HOST, realsense.PORT)
        darknet_detect(net, meta, rgbd, annotator, thresh=args.thresh)
        cv2.waitKey(0)
