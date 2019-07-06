import pickle
import socket

import cv2
import numpy as np

INPUT_MAP = [[200, 10], [1080, 10], [1270, 710], [10, 710]]
OUTPUT_MAP = [[0, 0], [1280, 0], [1280, 720], [0, 720]]
RESOLUTION = (1280, 720)
COLORS = [
    [31, 119, 180, 255],
    [174, 199, 232, 255],
    [255, 127, 14, 255],
    [255, 187, 120, 255],
    [44, 160, 44, 255],
    [152, 223, 138, 255],
    [214, 39, 40, 255],
    [255, 152, 150, 255],
    [148, 103, 189, 255],
    [197, 176, 213, 255],
    [140, 86, 75, 255],
    [196, 156, 148, 255],
    [227, 119, 194, 255],
    [247, 182, 210, 255],
    [127, 127, 127, 255],
    [199, 199, 199, 255],
    [188, 189, 34, 255],
    [219, 219, 141, 255],
    [23, 190, 207, 255],
    [158, 218, 229, 255],
]


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
    rgb, d = rgbd[:, :, :3].astype(np.uint8), rgbd[:, :, 3]
    rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
    return rgb, d


def predict(net, meta, annotator, thresh=0.05, show=True):
    rgbd = realsense.get_frames()
    rgb, d = split_rgbd(rgbd)
    cv2.imwrite(".tmp/frame.jpg", rgb)
    preds = darknet.detect(net, meta, ".tmp/frame.jpg".encode("ascii"), thresh=thresh)
    if show:
        annotator.add_patches(preds, rgb, d)
        cv2.imshow("darknet", rgb)
    return preds


def livestream(net, meta, annotator, thresh=0.05, fps=24):
    delay = int(100 / fps)
    while True:
        predict(net, meta, annotator)
        if cv2.waitKey(delay) == ord("q"):
            break
    cv2.destroyAllWindows()


class Annotator:
    def __init__(self, path2names, font=cv2.FONT_HERSHEY_DUPLEX, colors=COLORS):
        self.names = load_names(path2names)
        self.colors = colors
        self.font = font

    def add_circles(self, img, input_map=INPUT_MAP):
        for point in input_map:
            cv2.circle(img, tuple(point), 5, (0, 0, 255), -1)

    def add_patches(self, preds, rgb, d):
        for label, confidence, coords in preds:
            x, y, width, height = coords
            x1, y1, = int(x - width / 2), int(y - height / 2)
            x2, y2 = int(x + width / 2), int(y + height / 2)

            label = label.decode("utf-8")
            distance = round(d[int(y), int(x)] / 1000, 2)
            color = self.colors[self.names.index(label)][:3]
            s = "{} (Conf.: {}, Dist.: {} m)".format(label, round(confidence, 2), distance)

            cv2.putText(rgb, s, (x1 + 5, y1 - 5), self.font, 0.5, color, 1)
            cv2.rectangle(rgb, (x1, y1), (x2, y2), color, 2)
            cv2.circle(rgb, (int(x), int(y)), 5, color, -1)
