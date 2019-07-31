import argparse
import json
import subprocess
import sys
import time
from copy import deepcopy
from datetime import datetime
from multiprocessing import Process

import cv2

from robot import realsense, respeaker, romeo, xpad
from robot.helpers import connect_and_send, get_data
from sound.gunshot import Gunshot
from sound.sentiment import Sentiment
from vision.helpers import split_rgbd
from vision.tracker import Tracker
from vision.yolo import YoloV3
from vision.store_args import StoreArgs

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", action="store_true")
    parser.add_argument("--app", action="store_true")
    args = parser.parse_args()

    devices = {
        "ReSpeaker": respeaker.ReSpeaker(),
        "Romeo": romeo.Romeo()
    }

    d435i = realsense.D435i()
    yolov3 = YoloV3()
    tracker = Tracker()
    sentiment = Sentiment()
    gunshot = Gunshot()

    processes = {}

    for name, device in devices.items():
        processes[name] = Process(target=device.run)

    for name, process in processes.items():
        print("Starting {} ...".format(name))
        process.start()

    time.sleep(5)

    try:
        delay = int(1 / realsense.FPS)
        while True:
            samples = get_data(respeaker.HOST, respeaker.PORT)
            direction = respeaker.api.direction

            emotion, confidence = sentiment.detect(samples[:, 0])
            is_gunshot = gunshot.detect(samples[:, 0])

            frames = d435i._get_frames()
            frames = d435i._frames_to_rgbd(frames)

            rgb, depth = split_rgbd(frames)
            rgb, markers = tracker.detect(rgb, depth)
            rgb, detections = yolov3.detect(rgb, depth)

            cv2.imshow("devastator", rgb)
            if cv2.waitKey(delay) == ord("q"):
                break
    finally:
        cv2.destroyAllWindows()
        for name, process in processes.items():
            print("Stopping {}".format(name))
            process.terminate()
