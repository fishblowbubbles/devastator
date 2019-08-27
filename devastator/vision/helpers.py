import pickle
import socket
from collections import namedtuple

import cv2
import cv2.aruco as aruco
import numpy as np

from robot import realsense
from robot.helpers import get_data

INPUT_MAP = [[200, 10], [1080, 10], [1270, 710], [10, 710]]
OUTPUT_MAP = [[0, 0], [1280, 0], [1280, 720], [0, 720]]
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
FONT = cv2.FONT_HERSHEY_DUPLEX

Detection = namedtuple("Detection",
                       ("label", "confidence", "coords", "distance"))


def fix_perspective(img, src=INPUT_MAP, dst=OUTPUT_MAP,
                    resolution=realsense.RESOLUTION):
    src, dst = np.float32(src), np.float32(dst)
    M = cv2.getPerspectiveTransform(src, dst)
    rectified = cv2.warpPerspective(img, M, resolution)
    return rectified


def split_rgbd(frames):
    rgb = frames[:, :, :3].astype(np.uint8)
    rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
    depth = frames[:, :, 3]
    return rgb, depth


def get_distance(x, y, depth):
    distance = round(depth[int(y), int(x)] / 1000, 2)
    return distance


def add_distances(detections, depth):
    detections_with_distances = []
    for label, confidence, coords in detections:
        x, y, _, _ = coords
        distance = get_distance(x, y, depth)
        detection = Detection(label.decode("utf-8"), confidence,
                              coords, distance)
        detections_with_distances.append(detection)
    return detections_with_distances


def livestream(detect, fps=realsense.FPS, **kwargs):
    delay = int(100 / fps)
    while True:
        rgbd = get_data(realsense.HOST, realsense.PORT)
        rgb, depth = split_rgbd(rgbd)
        rgb, _ = detect(rgb, depth, **kwargs)
        cv2.imshow("livestream", rgb)
        if cv2.waitKey(delay) == ord("q"):
            break
    cv2.destroyAllWindows()


def load_names(path_to_names):
    names = []
    with open(path_to_names, "r") as file:
        lines = file.read()
        lines = lines.strip().split("\n")
        for line in lines:
            names.append(line)
    return names


def draw_detections(rgb, detections, names, colors=COLORS, font=FONT):
    for detection in detections:
        x, y, width, height = detection.coords
        x1, y1, = int(x - width / 2), int(y - height / 2)
        x2, y2 = int(x + width / 2), int(y + height / 2)

        color = colors[names.index(detection.label)][:3]
        s = "{} (Conf.: {}, Dist.: {} m)".format(detection.label,
                                                round(detection.confidence, 2),
                                                detection.distance)

        cv2.putText(rgb, s, (x1 + 5, y1 - 5), font, 0.5, color, 1)
        cv2.rectangle(rgb, (x1, y1), (x2, y2), color, 2)
        cv2.circle(rgb, (int(x), int(y)), 5, color, -1)


def draw_markers(rgb, markers, corners, font=FONT):
    for marker in markers:
        x = int(marker["corners"][0][0][0]) + 5
        y = int(marker["corners"][0][0][1]) - 5
        s = "Dist.: {} m, Angle: {}".format(marker["distanceToMarker"],
                                            marker["angleToMarker"])
        cv2.putText(rgb, s, (x, y), font, 0.5, (0, 255, 0), 1)
    aruco.drawDetectedMarkers(rgb, corners)
