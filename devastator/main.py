import sys

sys.path.remove("/opt/intel/openvino_2019.2.242/python/python3.5")
sys.path.remove("/opt/intel/openvino_2019.2.242/python/python3")

import argparse
import os
import sys
import time
from datetime import datetime
from multiprocessing import Process

import cv2
import numpy as np

from robot import realsense, respeaker, romeo, xpad
from robot.helpers import connect_and_send, get_data
from navigation.controllers import FullStateFeedbackController
from sound.gunshot import Gunshot
from sound.sentiment import Sentiment
from vision.helpers import split_rgbd
from vision.store_args import StoreArgs
from vision.tracker import Tracker
from vision.yolo import YoloV3

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", action="store_true")
    parser.add_argument("--app", action="store_true")
    args = parser.parse_args()

    devices = {
        # "RealSense": realsense.D435i(),
        "ReSpeaker": respeaker.ReSpeaker(),
        "Romeo": romeo.Romeo(),
        # "XPad": xpad.XPad(romeo.HOST, romeo.PORT)
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
    scanned = False

    def detect():
        samples = get_data(respeaker.HOST, respeaker.PORT)
        direction = respeaker.api.direction
        if direction > 180:
            direction -= 360

        emotion, confidence = sentiment.detect(samples[:, 0])
        is_gunshot = gunshot.detect(samples[:, 0])
        
        print("Emotion: {}, Confidence: {:5.2}".format(emotion, float(confidence)))
        print("Gunshot?: {}".format(is_gunshot))
        print("Direction: {}".format(direction))

        frames = d435i._get_frames()
        frames = d435i._frames_to_rgbd(frames)

        rgb, depth = split_rgbd(frames)
        rgb, markers = tracker.detect(rgb, depth)
        rgb, detections = yolov3.detect(rgb, depth)
        
        marker = {}
        for m in markers:
            if m["id"] == route[index]:
                marker = m

        for detection in detections:
            h_angle = detection["h_angle"]
            if direction < h_angle + 20 and direction > h_angle - 20:
                detection["emotion"] = emotion
                for e in detection["equip"]:
                    if e["label"] == "Rifle" or e["label"] == "Handgun":
                        e["gunshot"] = is_gunshot
                        e["direction"] = direction
            else:
                detection["emotion"] = '-'

        print("Marker: {}".format(marker))
        print("Detections: {}".format(detections))

        if marker:
            marker["objectsDetected"] = detections
            connect_and_send(marker, host="192.168.1.136", port=8998)
        
        if detections:
            connect_and_send(detections, host="192.168.1.136", port=8888)

        return rgb

    try:
        delay = int(100 / realsense.FPS)
        route = [2, 3, 4]
        complete = False
        index = 0
        while True:
            # for _ in range(50):
            frames = d435i._get_frames()
            frames = d435i._frames_to_rgbd(frames)

            rgb, depth = split_rgbd(frames)
            rgb, markers = tracker.detect(rgb, depth)

            marker = {}
            for m in markers:
                if m["id"] == route[index]:
                    marker = m

            print("Marker: {}".format(marker))

            if marker:
                # print("Heading towards marker {} ...".format(marker["id"]))
                # connect_and_send({10: {3: 1}}, romeo.HOST, romeo.PORT) # revert to automatic

                # y = {'y' : np.array([[marker["distanceToMarker"]],
                                    #  [marker["angleToMarker"] * 0.01745329252]])}
                # connect_and_send(y, host="localhost", port=56790)

                marker["objectsDetected"] = []
                connect_and_send(marker, host="192.168.1.136", port=8998)
                if marker["distanceToMarker"] < 1.0:
                    # connect_and_send({7: {1: 0}}, romeo.AUTO_HOST, romeo.AUTO_PORT)
                    # for _ in range(6):
                    #     connect_and_send({7: {3: -0.85}}, romeo.HOST, romeo.AUTO_PORT)
                    #     time.sleep(1)
                    #     connect_and_send({7: {3: 0}}, romeo.HOST, romeo.AUTO_PORT)
                    #     rgb = detect()

                    #     cv2.imshow("devastator", rgb)
                    #     if cv2.waitKey(delay) == ord("q"):
                    #         break
                    if index < len(route) - 1:
                        print("Heading to next marker ...")
                        scanned = False
                        index += 1
                    else:
                        print("Route complete, stopping ...")
                        connect_and_send({7: {1: 0}}, romeo.AUTO_HOST, romeo.AUTO_PORT)
                        complete = True
                elif marker["angleToMarker"] > 5:
                    print("Turning left!")
                    connect_and_send({7: {1: 0}}, romeo.AUTO_HOST, romeo.AUTO_PORT)
                    connect_and_send({7: {3: 0.40}}, romeo.AUTO_HOST, romeo.AUTO_PORT) # turn left
                    time.sleep(0.25)
                    connect_and_send({7: {3: 0}}, romeo.AUTO_HOST, romeo.AUTO_PORT)
                elif marker["angleToMarker"] < -5:
                    print("Turning right!")
                    connect_and_send({7: {1: 0}}, romeo.AUTO_HOST, romeo.AUTO_PORT)
                    connect_and_send({7: {3: -0.40}}, romeo.AUTO_HOST, romeo.AUTO_PORT) # turn right
                    time.sleep(0.25)
                    connect_and_send({7: {3: 0}}, romeo.AUTO_HOST, romeo.AUTO_PORT)
                else:
                    print("Going forward!")
                    if not scanned:
                        print("detecting ...")
                        # for _ in range(5):
                        rgb = detect()
                            # cv2.imshow("devastator", rgb)
                            # if cv2.waitK.ey(delay) == ord("q"):
                                # break
                        scanned = True
                    connect_and_send({7: {1: -0.4}}, romeo.AUTO_HOST, romeo.AUTO_PORT) # forward
                    time.sleep(0.25)
            else:
                print("Searching for marker ...")
                # connect_and_send({10: {2: 1}}, romeo.HOST, romeo.PORT) # send manual controls
                if not complete:
                    connect_and_send({7: {1: 0}}, romeo.AUTO_HOST, romeo.AUTO_PORT)
                    connect_and_send({7: {3: -0.5}}, romeo.AUTO_HOST, romeo.AUTO_PORT)
                    time.sleep(0.2)
                    connect_and_send({7: {3: 0}}, romeo.AUTO_HOST, romeo.AUTO_PORT)
                    time.sleep(0.3)
                    # connect_and_send({7: {1: 0}}, romeo.HOST, romeo.PORT)
                    # connect_and_send({7: {3: -0.5}}, romeo.HOST, romeo.PORT)
                    # time.sleep(0.5)
                    # connect_and_send({7: {3: 0}}, romeo.HOST, romeo.PORT)
                    # time.sleSep(0.2)

            cv2.imshow("devastator", rgb)
            if cv2.waitKey(delay) == ord("q"):
                break
            
            # rgb = detect()

            # cv2.imshow("devastator", rgb)
            # if cv2.waitKey(delay) == ord("q"):
            #   break   
    finally:
        cv2.destroyAllWindows()
        d435i.pipeline.stop()
        for name, process in processes.items():
            print("Stopping {}".format(name))
            process.terminate()
