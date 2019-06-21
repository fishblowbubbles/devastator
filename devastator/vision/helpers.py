import pickle
import socket

import cv2
import numpy as np

INPUT_MAP = [[200, 10], [1080, 10], [1270, 710], [10, 710]]
OUTPUT_MAP = [[0, 0], [1280, 0], [1280, 720], [0, 720]]
RESOLUTION = (1280, 720)


def fix_perspective(img, src=INPUT_MAP, dst=OUTPUT_MAP, resolution=RESOLUTION):
    src, dst = np.float32(src), np.float32(dst)
    M = cv2.getPerspectiveTransform(src, dst)
    rectified = cv2.warpPerspective(img, M, resolution)
    return rectified
