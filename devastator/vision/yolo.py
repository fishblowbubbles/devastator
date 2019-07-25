import cv2

from robot.helpers import get_data
from vision.darknet import darknet
from vision.helpers import add_distances, draw_detections, load_names, split_rgbd


PATH_TO_WEIGHTS = "devastator/vision/darknet/backup/custom.weights"
PATH_TO_NAMES = "devastator/vision/darknet/data/custom.names"
PATH_TO_DATA = "devastator/vision/darknet/cfg/custom.data"
PATH_TO_CFG = "devastator/vision/darknet/cfg/custom.cfg"

THRESHOLD = 0.1


class Darknet:
    def __init__(self, filename=".tmp/frame.jpg"):
        self.net = darknet.load_net(PATH_TO_CFG.encode("ascii"),
                                    PATH_TO_WEIGHTS.encode("ascii"), 0)
        self.meta = darknet.load_meta(PATH_TO_DATA.encode("ascii"))
        self.names = load_names(PATH_TO_NAMES)
        self.filename = filename

    def detect(self, rgb, depth, threshold=THRESHOLD, show=False):
        cv2.imwrite(self.filename, rgb)
        detections = darknet.detect(self.net, self.meta,
                                    self.filename.encode("ascii"),
                                    thresh=threshold)
        detections = add_distances(detections, depth)
        draw_detections(rgb, detections, self.names)
        if show:
            cv2.imshow("darknet", rgb)
        return rgb, detections
