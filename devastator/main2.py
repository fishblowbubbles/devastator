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
from vision.yolo import Darknet
from vision.store_args import StoreArgs

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", action="store_true")
    parser.add_argument("--app", action="store_true")
    args = parser.parse_args()

    if args.robot:
        d435i = realsense.D435i()
        devices = {
            "ReSpeaker": respeaker.ReSpeaker(),
            "Romeo": romeo.Romeo()
        }
        # yolo = YOLO()
        # darknet = Darknet()
        tracker = Tracker()
        sentiment = Sentiment()
        gunshot = Gunshot()
    elif args.app:
        devices = {
            "XPad": xpad.XPad()
        }
    else:
        parser.print_help()
        sys.exit()

    processes = {}

    for name, device in devices.items():
        processes[name] = Process(target=device.run)

    for name, process in processes.items():
        print("Starting {} ...".format(name))
        process.start()

    time.sleep(5)

    try:
        delay = int(100 / realsense.FPS)
        while True:
            samples = get_data(respeaker.HOST, respeaker.PORT)
            direction = respeaker.api.direction

            emotion, confidence = sentiment.detect(samples[:, 0])
            is_gunshot = gunshot.detect(samples[:, 0])

            frames = d435i._get_frames()
            frames = d435i._frames_to_rgbd(frames)

            rgb, depth = split_rgbd(frames)
            # rgb, detections = darknet.detect(rgb, depth)
            rgb, markers = tracker.detect(rgb, depth)

            new_data = {
                "data": {
                    0: {
                        "Time_Stamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Threat_Direction": direction,
                        "Emotions_Present": emotion,  # str(emotions)?
                        "Gunshots": is_gunshot,
                        "Objects_Of_Interest": "",
                        "More_Details": "<a href= www.google.com.sg>www.viewmorehere.com  </a>"
                    }
                }
            }

            print(new_data)

            connect_and_send(new_data, "192.168.1.136", 8888)

            cv2.imshow("devastator", rgb)
            if cv2.waitKey(delay) == ord("q"):
                break
    finally:
        for name, process in processes.items():
            print("Stopping {}".format(name))
            process.terminate()
