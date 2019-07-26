import argparse
import sys

sys.path.append("./devastator")

import cv2

import robot.realsense as realsense
from robot.helpers import get_data
from vision.helpers import livestream, split_rgbd
from vision.tracker import Tracker

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--fps", type=int, default=realsense.FPS)
    parser.add_argument("--resolution", type=tuple,
                        default=realsense.RESOLUTION)
    parser.add_argument("--fov", type=float, default=realsense.FOV)
    args = parser.parse_args()

    tracker = Tracker(resolution=args.resolution, fov=args.fov)
    if args.video:
        livestream(tracker.detect, fps=args.fps)
    else:
        frames = get_data(realsense.HOST, realsense.PORT)
        rgb, depth = split_rgbd(frames)
        tracker.detect(rgb, depth)
        cv2.waitKey(0)