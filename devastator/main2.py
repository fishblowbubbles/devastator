import sys

"""
oldpath = [
    '', 
    '/opt/intel/openvino_2019.2.242/python/python3.5', # has openvino
    '/opt/intel/openvino_2019.2.242/python/python3', # no openvino
    '/opt/intel/openvino_2019.2.242/deployment_tools/model_optimizer', # no openvino
    '/home/s04/catkin_ws/devel/lib/python2.7/dist-packages', #
    '/opt/ros/kinetic/lib/python2.7/dist-packages', 
    '/usr/lib/python35.zip', 
    '/usr/lib/python3.5', 
    '/usr/lib/python3.5/plat-x86_64-linux-gnu', 
    '/usr/lib/python3.5/lib-dynload', 
    '/home/s04/.local/lib/python3.5/site-packages', 
    '/usr/local/lib/python3.5/dist-packages', 
    '/usr/lib/python3/dist-packages'
]

print('s - o = {}\n'.format(set(sys.path) - set(oldpath)))
print('o - s = {}\n'.format(set(oldpath) - set(sys.path)))
print('s = {}\n'.format(sys.path))
print('o = {}\n'.format(oldpath))

sys.path = [
    '', 
    '/opt/intel/openvino_2019.2.242/python/python3.5', # has openvino
    '/opt/intel/openvino_2019.2.242/python/python3', # no openvino
    '/opt/intel/openvino_2019.2.242/deployment_tools/model_optimizer', # no openvino
    '/home/s04/catkin_ws/devel/lib/python2.7/dist-packages', #
    '/opt/ros/kinetic/lib/python2.7/dist-packages', 
    '/usr/lib/python35.zip', 
    '/usr/lib/python3.5', 
    '/usr/lib/python3.5/plat-x86_64-linux-gnu', 
    '/usr/lib/python3.5/lib-dynload', 
    '/home/s04/.local/lib/python3.5/site-packages', 
    '/usr/local/lib/python3.5/dist-packages', 
    '/usr/lib/python3/dist-packages'
]

print('sys.path = {}'.format(sys.path))
"""
#sys.path = list(dict.fromkeys(sys.path)) # remove duplicates

#sys.path.insert(1, '/opt/intel/openvino_2019.2.242/deployment_tools/model_optimizer')
#sys.path.insert(1, '/opt/intel/openvino_2019.2.242/python/python3')
#sys.path.insert(1, '/opt/intel/openvino_2019.2.242/python/python3.5')

sys.path.remove("/opt/intel/openvino_2019.2.242/python/python3.5")
sys.path.remove("/opt/intel/openvino_2019.2.242/python/python3")

import argparse
import os
import sys
import time
from datetime import datetime
from multiprocessing import Process

import cv2

from robot import realsense, respeaker, romeo, xpad
from robot.helpers import connect_and_send, get_data
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
        "ReSpeaker": respeaker.ReSpeaker(),
        "Romeo": romeo.Romeo()
    }

    d435i = realsense.D435i()

    # yolov3 = YoloV3()
    tracker = Tracker()
    sentiment = Sentiment()
    gunshot = Gunshot()

    processes = {}

    for name, device in devices.items():
        processes[name] = Process(target=device.run)

    for name, process in processes.items():
        print("Starting {} ...".format(name))
        process.start()

    time.sleep(2)

    try:
        delay = int(100 / realsense.FPS)
        
        route = [0, 1, 2, 3]
        index = 0 

        target_host = "192.168.1.136" 
        target_port = 8998

        while True:
            samples = get_data(respeaker.HOST, respeaker.PORT)
            # direction = respeaker.api.direction

            emotion, confidence = sentiment.detect(samples[:, 0])
            is_gunshot = gunshot.detect(samples[:, 0])
            
            print("Emotion: {}, Confidence: {:5.2}".format(emotion, float(confidence)))
            print("Gunshot?: {}".format(is_gunshot))

            frames = d435i._get_frames()
            frames = d435i._frames_to_rgbd(frames)

            rgb, depth = split_rgbd(frames)
            rgb, markers = tracker.detect(rgb, depth)
            # rgb, detections = yolov3.detect(rgb, depth)

            print("Markers: {}".format(markers))
            # print("Detections: {}".format(detections))

            # marker = markers[route[index]]
            if markers:
                connect_and_send(markers[0], target_host, target_port)

            cv2.imshow("devastator", rgb)
            if cv2.waitKey(delay) == ord("q"):
                break   
    finally:
        cv2.destroyAllWindows()
        for name, process in processes.items():
            print("Stopping {}".format(name))
            process.terminate()
