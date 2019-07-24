import pickle
import socket
from collections import namedtuple

import cv2
import numpy as np

from robot import realsense
from robot.helpers import get_data
from vision.darknet import darknet

INPUT_MAP = [[200, 10], [1080, 10], [1270, 710], [10, 710]]
OUTPUT_MAP = [[0, 0], [1280, 0], [1280, 720], [0, 720]]
RESOLUTION = (1280, 720)
COLORS = [[31 , 119, 180, 255], [174, 199, 232, 255],
          [255, 127, 14 , 255], [255, 187, 120, 255],
          [44 , 160, 44 , 255], [152, 223, 138, 255],
          [214, 39 , 40 , 255], [255, 152, 150, 255],
          [148, 103, 189, 255], [197, 176, 213, 255],
          [140, 86 , 75 , 255], [196, 156, 148, 255],
          [227, 119, 194, 255], [247, 182, 210, 255],
          [127, 127, 127, 255], [199, 199, 199, 255],
          [188, 189, 34 , 255], [219, 219, 141, 255],
          [23 , 190, 207, 255], [158, 218, 229, 255]]

Detection = namedtuple("Detection",
                       ("label", "confidence", "coords", "distance", "angle"))


def load_names(path):
    names = []
    with open(path, "r") as file:
        lines = file.read()
        lines = lines.strip().split("\n")
        for line in lines:
            names.append(line)
    return names


def fix_perspective(img, src=INPUT_MAP, dst=OUTPUT_MAP, resolution=RESOLUTION):
    src, dst = np.float32(src), np.float32(dst)
    M = cv2.getPerspectiveTransform(src, dst)
    rectified = cv2.warpPerspective(img, M, resolution)
    return rectified


def split_rgbd(rgbd):
    rgb, depth = rgbd[:, :, :3].astype(np.uint8), rgbd[:, :, 3]
    rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
    return rgb, depth


def load_darknet():
    net = darknet.load_net(darknet.PATH2CFG.encode("ascii"), darknet.PATH2WEIGHTS.encode("ascii"), 0)
    meta = darknet.load_meta(darknet.PATH2DATA.encode("ascii"))
    annotator = Annotator(path2names=darknet.PATH2NAMES)
    return net, meta, annotator


def darknet_detect(net, meta, rgbd, annotator, filename=".tmp/frame.jpg", thresh=0.05, show=True):
    rgb, depth = split_rgbd(rgbd)
    cv2.imwrite(filename, rgb)

    detections = darknet.detect(net, meta, filename.encode("ascii"), thresh=thresh)
    detections_with_distances = add_distances(detections, depth)

    if show:
        annotator.add_patches(detections_with_distances, rgb, depth)
        cv2.imshow("darknet", rgb)

    return detections


def darknet_livestream(net, meta, annotator, thresh=darknet.THRESH, fps=darknet.FPS):
    delay = int(100 / fps)
    while True:
        rgbd = get_data(realsense.HOST, realsense.PORT)
        darknet_detect(net, meta, rgbd, annotator, thresh=thresh)
        if cv2.waitKey(delay) == ord("q"):
            break
    cv2.destroyAllWindows()


def get_distance(x, y, depth):
    distance = round(depth[int(y), int(x)] / 1000, 2)
    return distance


def add_distances(detections, depth):
    detections_with_distances = []
    for label, confidence, coords in detections:
        x, y, _, _ = coords
        distance = get_distance(x, y, depth)
        detection = Detection(label.decode("utf-8"), confidence, coords, distance)
        detections_with_distances.append(detection)
    return detections_with_distances


class Annotator:
    def __init__(self, path2names, font=cv2.FONT_HERSHEY_DUPLEX, colors=COLORS):
        self.names = load_names(path2names)
        self.colors = colors
        self.font = font

    def add_circles(self, img, input_map=INPUT_MAP):
        for point in input_map:
            cv2.circle(img, tuple(point), 5, (0, 0, 255), -1)

    def add_patches(self, detections_with_distances, rgb, depth):
        for detection in detections_with_distances:
            x, y, width, height = detection.coords
            x1, y1, = int(x - width / 2), int(y - height / 2)
            x2, y2 = int(x + width / 2), int(y + height / 2)

            color = self.colors[self.names.index(detection.label)][:3]
            s = "{} (Conf.: {}, Dist.: {} m)".format(detection.label,
                                                     round(detection.confidence, 2),
                                                     detection.distance)

            cv2.putText(rgb, s, (x1 + 5, y1 - 5), self.font, 0.5, color, 1)
            cv2.rectangle(rgb, (x1, y1), (x2, y2), color, 2)
            cv2.circle(rgb, (int(x), int(y)), 5, color, -1)
