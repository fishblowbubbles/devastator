import argparse
import sys

sys.path.append("./devastator")

import cv2
import numpy as np

import robot.realsense as realsense
from robot.helpers import get_data
from vision.darknet import darknet
from vision.helpers import Annotator, darknet_detect, darknet_livestream, load_darknet

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--fps", type=int, default=darknet.FPS)
    parser.add_argument("--thresh", type=float, default=darknet.THRESH)
    args = parser.parse_args()

    net, meta, annotator = load_darknet()
    if args.video:
        darknet_livestream(net, meta, annotator, thresh=args.thresh, fps=args.fps)
    else:
        rgbd = get_data(realsense.HOST, realsense.PORT)
        darknet_detect(net, meta, rgbd, annotator, thresh=args.thresh)
        cv2.waitKey(0)
