import argparse
import json
import sys
import time
from multiprocessing import Process

import cv2

import robot.realsense as realsense
import robot.respeaker as respeaker
import robot.romeo as romeo
import robot.xpad as xpad
from robot.helpers import get_data, connect_and_send
from robot.realsense import D435i
from robot.respeaker import ReSpeaker
from robot.romeo import Romeo
from robot.xpad import XPad
from sound.helpers import emotion_detect, gunshot_detect, vokaturi_func
from vision.call_yolo import detect, get_frame, load_model, main
from vision.store_args import StoreArgs
from vision.Aruco_Tracker.aruco_tracker import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", action="store_true")
    parser.add_argument("--app", action="store_true")
    args = parser.parse_args()

    if args.robot:
        with open(StoreArgs.labels, 'r') as f:
            labels_map = [x.strip() for x in f]
        net, exec_net = load_model(StoreArgs.device, StoreArgs.labels, StoreArgs.model_xml, StoreArgs.model_bin, StoreArgs.plugin_dir, StoreArgs.cpu_extension)
        devices = {
            "RealSense": realsense.D435i(),
            "Romeo": romeo.Romeo(),
            "ReSpeaker": respeaker.ReSpeaker()
        }
        # darknet, tracker = Darknet(), Tracker()
        # emotion, gunshot = Emotion(), Gunshot()
        reportLogs = StoreArgs()
    elif args.app:
        devices = {
            # "App": app.App(),
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
        while True:
            samples = get_data(respeaker.HOST, respeaker.PORT)
            direction = respeaker.api.direction

            gunshot = gunshot_detect(samples[:, 0])
            if gunshot:
                print("Gunshots: {:10}\tDirection: {:10}"
                      .format(gunshot, direction))

            voice = respeaker.api.is_voice()
            if voice:
                emotion, confidence = emotion_detect(samples[:, 0])
                print("Emotion: {:10}\tConfidence: {:10.2}\tDirection: {:10}"
                      .format(emotion, confidence, direction))
####-------------------------- Realsense integration with report ui ----------------------------
            frame = get_data(realsense.HOST, realsense.PORT)
            detection, timestamp = detect(frame, net, exec_net, StoreArgs.labels_map, StoreArgs.prob_threshold,
                                          StoreArgs.iou_threshold,
                                          depth_given=True)  # gives a list of dictionaries #gives people

            reportLogs.obj_report_info() #dump files to json

            ### ------------------------- aruco tracker stuff --------------------------------------------



    finally:
        for name, process in processes.items():
            print("Stopping {}".format(name))
