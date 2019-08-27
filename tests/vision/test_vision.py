import argparse
import sys

sys.path.append("./devastator")

import cv2

import robot.realsense as realsense
from robot.helpers import get_data
from vision.helpers import split_rgbd
from vision.tracker import Tracker
from vision.yolo import YoloV3

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fps", type=int, default=realsense.FPS)
    args = parser.parse_args()

    yolov3, tracker = YoloV3(), Tracker()
    delay = int(100 / args.fps)

    while True:
        frames = get_data(realsense.HOST, realsense.PORT)
        rgb, depth = split_rgbd(frames)
        rgb, detections = yolov3.detect(rgb, depth)
        rgb, markers = tracker.detect(rgb, depth)

        cv2.imshow("vision", rgb)
        if cv2.waitKey(delay) == ord("q"):
            break
