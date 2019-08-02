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
    parser.add_argument("--calibrate", action="store_true")
    parser.add_argument("--distance", type=float)
    args = parser.parse_args()

    tracker = Tracker(resolution=args.resolution, fov=args.fov)
    if args.video:
        livestream(tracker.detect, fps=args.fps)
    elif args.calibrate:
        frames = get_data(realsense.HOST, realsense.PORT)
        rgb, depth = split_rgbd(frames)
        rgb, focal_length = tracker.calibrate(rgb, args.distance)
        print("Focal Length: {}".format(focal_length))
        cv2.imshow("tracker", rgb)
        cv2.waitKey(0)
