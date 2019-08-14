import os

import cv2

from robot.helpers import get_data
# from vision.darknet import darknet
from vision.call_yolo import detect, load_model
from vision.helpers import add_distances, draw_detections, load_names, split_rgbd


PATH_TO_WEIGHTS = "devastator/vision/darknet/backup/custom.weights"
PATH_TO_NAMES = "devastator/vision/darknet/data/custom.names"
PATH_TO_DATA = "devastator/vision/darknet/cfg/custom.data"
PATH_TO_CFG = "devastator/vision/darknet/cfg/custom.cfg"

THRESHOLD = 0.1


# class Darknet:
#     def __init__(self, filename=".tmp/frame.jpg"):
#         self.net = darknet.load_net(PATH_TO_CFG.encode("ascii"),
#                                     PATH_TO_WEIGHTS.encode("ascii"), 0)
#         self.meta = darknet.load_meta(PATH_TO_DATA.encode("ascii"))
#         self.names = load_names(PATH_TO_NAMES)
#         self.filename = filename

#     def detect(self, rgb, depth, threshold=THRESHOLD):
#         cv2.imwrite(self.filename, rgb)
#         detections = darknet.detect(self.net, self.meta,
#                                     self.filename.encode("ascii"),
#                                     thresh=threshold)
#         detections = add_distances(detections, depth)
#         draw_detections(rgb, detections, self.names)
#         return rgb, detections


device = 'CPU'  # GPU
labels = './custom.names'  # set to None if no labels
cpu_extension = '/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/libcpu_extension_sse4.so'
model_xml = './YoloV2_40000.xml'
model_bin = os.path.splitext(model_xml)[0] + ".bin"


class YoloV3:
    def __init__(self):
        print("Loading YoloV3 ... ", end="")
        self.net, self.exec = load_model(device, labels, model_xml, model_bin,
                                         plugin_dir=None, cpu_extension=cpu_extension)
        print("done!")
        with open(labels, 'r') as f:
            self.labels_map = [x.strip() for x in f]

    def detect(self, rgb, depth, threshold=THRESHOLD):
        rgb, detections = detect(rgb, depth, self.net, self.exec, self.labels_map,
                                 prob_thresh=0.1, iou_thresh=0.4,
                                 depth_given=True)
        return rgb,  detections
