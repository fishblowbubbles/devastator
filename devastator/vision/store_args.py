#might not need this? but just leave here first

import os
import json
from robot.helpers import get_data

# INPUT_STREAM = "cam"
# HOST = "localhost" #host and port of mini_map_new.py
# # PORT = 8898 #host and port of mini_map_new.py

DEVICE = 'CPU' #GPU
LABELS = './custom.names'  # set to None if no labels
CPU_EXTENSION = '/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/libcpu_extension_sse4.so'
MODEL_XML = './YoloV2_18000.xml'
MODEL_BIN = os.path.splitext(MODEL_XML)[0] + ".bin"
PROB_THRESH = 0.5
IOU_THRESH = 0.4
LABELS_MAP = ''
# DEPTH_GIVEN = False
PLUGIN_DIR = None
RIFLE_COUNT = 0
HANDGUN_COUNT = 0
KNIFE_COUNT = 0
JACKET_COUNT = 0
HAT_COUNT = 0
SUN_GLASSES_COUNT = 0
PERSON_COUNT = 0
POLICE_COUNT = 0
OBJ_OF_INTEREST = ""
NEW_KEY = 0 #for the json format numbering
OBJ_DISTANCE = 0.0
OBJ_ANGLE  = 0.0
OBJ_DANGER_SCORE = 0
OBJ_DETECTED = ""
ROBOT_ACTION = "Moving"


#----------------------- detection ------------------------

class StoreArgs:
    def __init__(self,
                 # input_stream=INPUT_STREAM,
                 # host=HOST,
                 # port=PORT,
                 device=DEVICE,
                 labels=LABELS,
                 cpu_extension=CPU_EXTENSION,
                 model_xml=MODEL_XML,
                 model_bin=MODEL_BIN,
                 labels_map=LABELS_MAP,
                 prob_thresh=PROB_THRESH,
                 iou_thresh=IOU_THRESH,
                 # depth_given=DEPTH_GIVEN,
                 plugin_dir=PLUGIN_DIR,
                 rifle_count=RIFLE_COUNT,
                 handgun_count=HANDGUN_COUNT,
                 person_count=PERSON_COUNT,
                 sunglass_count=SUN_GLASSES_COUNT,
                 jacket_count=JACKET_COUNT,
                 hat_count=HAT_COUNT,
                 police_count=POLICE_COUNT,
                 knife_count=KNIFE_COUNT,
                 obj_of_interest=OBJ_OF_INTEREST,
                 new_key=NEW_KEY,
                 object_distance = OBJ_DISTANCE,
                 object_angle = OBJ_ANGLE,
                 object_danger_score = OBJ_DANGER_SCORE,
                 object_detected = OBJ_DETECTED,
                 robot_action = ROBOT_ACTION

                 ):
        # self.input_stream = input_stream
        # self.host = host
        # self.port = port
        self.device = device
        self.labels = labels
        self.cpu_extension = cpu_extension
        self.model_xml = model_xml
        self.model_bin = model_bin
        self.labels_map = labels_map
        self.prob_thresh = prob_thresh
        self.iou_thresh = iou_thresh
        # self.depth_given = depth_given
        self.plugin_dir = plugin_dir
        self.rifle_count = rifle_count
        self.handgun_count = handgun_count
        self.person_count = person_count
        self.knife_count = knife_count
        self.police_count = police_count
        self.hat_count = hat_count
        self.jacket_count = jacket_count
        self.sunglass_count = sunglass_count
        self.new_key = new_key
        self.object_distance = object_distance
        self.object_angle = object_angle
        self.object_danger_score = object_danger_score
        self.object_detected = object_detected
        self.robot_action = robot_action


    def obj_report_info(self,detection,timestamp,direction,emotion,gunshot):
        #### assume data structure of detection is:
        #### eg. detection = [{"depth":0.762,"danger_score":3.44,"equip":[{"label":"Rifle","box":{}}],"label":"Person","box":{}},{"depth":0.762,"danger_score":3.44,"equip":[{"label":"Rifle","box":{}},{"label":"Handgun","box":{}}],"label":"Person","box":{}}]
        self.person_count = len(detection)
        detected_objects = []
        distance_to_obj = []
        angle_to_obj = []
        if len(detection) != 0:
            for i in detection:
                for j in i["equip"]:
                    if j["label"] == "Rifle":
                        self.rifle_count += 1

                    elif j["label"] == "Handgun":
                        self.handgun_count += 1

                    elif j["label"] == "Knife":
                        self.knife_count += 1

                    elif j["label"] == "Jacket":
                        self.jacket_count += 1

                    elif j["label"] == "Sunglasses":
                        self.sunglass_count += 1

                    elif j["label"] == "Police":
                        self.police_count += 1

                    elif j["label"] == "Hat":
                        self.hat_count += 1

                self.object_distance = i["depth"]
                self.object_angle = i["h_angle"]
                self.object_danger_score = i["danger_score"]

                if self.object_danger_score > 0.5:
                    self.object_detected = "THREAT"

                elif 0.3 <= self.object_danger_score <= 0.5:
                    self.object_detected = "SUSPECT"

                else:
                    self.object_detected = "PERSON"
                detected_objects.append(self.object_detected) #gives the list of people detected
                distance_to_obj.append(self.object_distance)
                angle_to_obj.append(self.object_angle)

            ###format the data for objects of interest to parse into report ui app
            self.obj_of_interest = "Handgun: " + str(self.handgun_count) + "  <p/> " + "Jacket: " + str(
                self.jacket_count) + " <p/> " + "Knife: " + str(
                self.knife_count) + " <p/> " + "Person: " + str(
                self.person_count) + " <p/> " + "Rifle " + str(self.rifle_count) + " <p/> " + "Sunglasses: " \
                                        + str(self.sunglass_count) + " <p/> " + "Police: " + str(
                self.police_count) + " <p/> "


            # new_json_info =  to append to current obj_of_interest?
            for keys in self.json_info['data']:
                keys = keys
                self.new_key = int(keys) + 1

            # take the latest new_key from above
            new_data = {
                str(self.new_key): {
                    "Time_Stamp": timestamp,
                    "Threat_Direction": direction,
                    "Emotions_Present": emotion,  # str(emotions)?
                    "Gunshots": gunshot,
                    "Objects_Of_Interest": self.obj_of_interest,
                    "More_Details": "<a href=dummylink>www.viewmorehere.com  </a>"
                }
            }

        else:
            self.object_detected = ""
            detected_objects=""

        return detected_objects,distance_to_obj,angle_to_obj,new_data