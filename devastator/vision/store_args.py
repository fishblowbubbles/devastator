#might not need this? but just leave here first

import os

# INPUT_STREAM = "cam"
# HOST = "localhost" #host and port of mini_map_new.py
# # PORT = 8898 #host and port of mini_map_new.py
# PORT = 4444 #port from call_yolo
# DEVICE = 'CPU' #GPU
# LABELS = './custom.names'  # set to None if no labels
# CPU_EXTENSION = '/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/libcpu_extension_sse4.so'
# MODEL_XML = './YoloV2_18000.xml'
# MODEL_BIN = os.path.splitext(MODEL_XML)[0] + ".bin"
# PROB_THRESH = 0.5
# IOU_THRESH = 0.4
# DEPTH_GIVEN = False
# PLUGIN_DIR = None

RIFLE_COUNT = 0
HANDGUN_COUNT = 0
KNIFE_COUNT = 0
JACKET_COUNT = 0
HAT_COUNT = 0
SUN_GLASSES_COUNT = 0
PERSON_COUNT = 0
POLICE_COUNT = 0
OBJ_OF_INTEREST = ""


#----------------------- detection ------------------------
# mapping labels
# with open(LABELS, 'r') as f:
#     LABELS_MAP = [x.strip() for x in f]

class StoreArgs:
    def __init__(self,
                 # input_stream=INPUT_STREAM,
                 # host=HOST,
                 # port=PORT,
                 # device=DEVICE,
                 # labels=LABELS,
                 # cpu_extension=CPU_EXTENSION,
                 # model_xml=MODEL_XML,
                 # model_bin=MODEL_BIN,
                 # labels_map=LABELS_MAP,
                 # prob_thresh=PROB_THRESH,
                 # iou_thresh=IOU_THRESH,
                 # depth_given=DEPTH_GIVEN,
                 # plugin_dir=PLUGIN_DIR,
                 rifle_count=RIFLE_COUNT,
                 handgun_count=HANDGUN_COUNT,
                 person_count=PERSON_COUNT,
                 sunglass_count=SUN_GLASSES_COUNT,
                 jacket_count=JACKET_COUNT,
                 hat_count=HAT_COUNT,
                 police_count=POLICE_COUNT,
                 knife_count=KNIFE_COUNT,
                 obj_of_interest=OBJ_OF_INTEREST

                 ):
        # self.input_stream = input_stream
        # self.host = host
        # self.port = port
        # self.device = device
        # self.labels = labels
        # self.cpu_extension = cpu_extension
        # self.model_xml = model_xml
        # self.model_bin = model_bin
        # self.labels_map = labels_map
        # self.prob_thresh = prob_thresh
        # self.iou_thresh = iou_thresh
        # self.depth_given = depth_given
        # self.plugin_dir = plugin_dir
        self.rifle_count = rifle_count
        self.handgun_count = handgun_count
        self.person_count = person_count
        self.knife_count = knife_count
        self.police_count = police_count
        self.hat_count = hat_count
        self.jacket_count = jacket_count
        self.sunglass_count = sunglass_count
        self.obj_of_interest = obj_of_interest
