import pickle
import socket

import cv2
import matplotlib.pyplot as plt
import numpy as np

INPUT_MAP = [[200, 10], [1080, 10], [1270, 710], [10, 710]]
OUTPUT_MAP = [[0, 0], [1280, 0], [1280, 720], [0, 720]]
RESOLUTION = (1280, 720)


def fix_perspective(img, src=INPUT_MAP, dst=OUTPUT_MAP, resolution=RESOLUTION):
    src, dst = np.float32(src), np.float32(dst)
    M = cv2.getPerspectiveTransform(src, dst)
    rectified = cv2.warpPerspective(img, M, resolution)
    return rectified


def load_names(path):
    names = []
    with open(path, "r") as file:
        lines = file.read()
        lines = lines.strip().split("\n")
        for line in lines:
            names.append(line)
    return names


def load_colors(n_classes):
    cmap = plt.get_cmap("rainbow")
    colors = [cmap(i) for i in np.linspace(0, 1, n_classes)]
    return colors


def add_circles(img, input_map=INPUT_MAP):
    for point in input_map:
        cv2.circle(img, tuple(point), 5, (0, 0, 255), -1)


def add_patches(preds, rgb, d, names, colors):
    for label, confidence, coords in preds:
        x, y, width, height = coords
        x1, y1, = int(x - width / 2), int(y - height / 2)
        x2, y2 = int(x + width / 2), int(y + height / 2)

        label = label.decode("utf-8")
        distance = round(d[int(y), int(x)] / 1000, 2)
        color = colors[names.index(label)][:3]
        color = [int(c * 255) for c in color]
        s = "{} (Conf.: {}, Dist.: {} m)".format(label, round(confidence, 2), distance)

        cv2.putText(rgb, s, (x1 + 5, y1 - 5), cv2.FONT_HERSHEY_DUPLEX, 0.5, color, 1)
        cv2.rectangle(rgb, (x1, y1), (x2, y2), color, 2)
        cv2.circle(rgb, (int(x), int(y)), 5, color, -1)
