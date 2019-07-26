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

            #### assume data structure of detection is:
            #### eg. detection = [{"depth":0.762,"danger_score":3.44,"equip":[{"label":"Rifle","box":{}}],"label":"Person","box":{}},{"depth":0.762,"danger_score":3.44,"equip":[{"label":"Rifle","box":{}},{"label":"Handgun","box":{}}],"label":"Person","box":{}}]
            StoreArgs.person_count = len(detection)

            if len(detection) != 0:
                for i in detection:
                    for j in i["equip"]:
                        if j["label"] == "Rifle":
                            StoreArgs.rifle_count += 1

                        elif j["label"] == "Handgun":
                            StoreArgs.handgun_count += 1

                        elif j["label"] == "Knife":
                            StoreArgs.knife_count += 1

                        elif j["label"] == "Jacket":
                            StoreArgs.jacket_count += 1

                        elif j["label"] == "Sunglasses":
                            StoreArgs.sunglass_count += 1

                        elif j["label"] == "Police":
                            StoreArgs.police_count += 1

                        elif j["label"] == "Hat":
                            StoreArgs.hat_count += 1

                    StoreArgs.object_distance = i["depth"]
                    StoreArgs.object_angle = i["h_angle"]
                    StoreArgs.object_danger_score = i["danger_score"]

                    if StoreArgs.object_danger_score > 0.5:
                        StoreArgs.object_detected = "THREAT"

                    elif 0.3 <= StoreArgs.object_danger_score <= 0.5:
                        StoreArgs.object_detected = "SUSPECT"

                    else:
                        StoreArgs.object_detected = "PERSON"

                ###format the data for objects of interest to parse into report ui app
                StoreArgs.obj_of_interest = "Handgun: " + str(StoreArgs.handgun_count) + "  <p/> " + "Jacket: " + str(
                    StoreArgs.jacket_count) + " <p/> " + "Knife: " + str(StoreArgs.knife_count) + " <p/> " + "Person: " + str(StoreArgs.person_count) + " <p/> " + "Rifle " + str(rifle_count) + " <p/> " + "Sunglasses: " \
                                            + str(StoreArgs.sunglass_count) + " <p/> " + "Police: " + str(StoreArgs.police_count) + " <p/> "
                # new_json_info =  to append to current obj_of_interest?
                for keys in StoreArgs.json_info['data']:
                    keys = keys
                    StoreArgs.new_key = int(keys) + 1

                # take the latest new_key from above
                new_data = {
                    str(StoreArgs.new_key): {
                        "Time_Stamp": timestamp,
                        "Threat_Direction": direction,
                        "Emotions_Present": emotion,  # str(emotions)?
                        "Gunshots": gunshot,
                        "Objects_Of_Interest": StoreAgs.obj_of_interest,
                        "More_Details": "<a href= www.google.com.sg>www.viewmorehere.com  </a>"
                    }
                }
                StoreArgs.json_info['data'].update(new_data)  # updates the json

                with open('../app/logs2.json', 'w') as outfile:
                    json.dump(StoreArgs.json_info, outfile,
                              indent=4)  # update the json file in app folder #for report logs ui
            else:
                StoreArgs.object_detected = ""

            ### ------------------------- aruco tracker stuff --------------------------------------------



    finally:
        for name, process in processes.items():
            print("Stopping {}".format(name))
