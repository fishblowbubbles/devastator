import argparse
import sys

sys.path.append("./devastator")

import cv2

import robot.realsense as realsense
from robot.helpers import get_data
from vision import yolo
from vision.helpers import livestream, split_rgbd

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--fps", type=int, default=realsense.FPS)
    parser.add_argument("--thresh", type=float, default=yolo.THRESH)
    args = parser.parse_args()

    darknet = yolo.Darknet()
    if args.video:
        livestream(darknet.detect, fps=args.fps)
    else:
        frames = get_data(realsense.HOST, realsense.PORT)
        rgb, depth = split_rgbd(frames)
        darknet.detect(rgb, depth, thresh=args.thresh)
        cv2.waitKey(0)
