import glob

import cv2
import cv2.aruco as aruco
import numpy as np

from robot import realsense
from robot.helpers import get_data
from vision.helpers import draw_markers, split_rgbd


class Tracker:
    def __init__(self, resolution=realsense.RESOLUTION, fov=realsense.FOV):
        self.resolution, self.fov = resolution, fov
        self.aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
        self.parameters = aruco.DetectorParameters_create()
        self.parameters.adaptiveThreshConstant = 10

    def detect(self, rgb, depth, show=False):
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        corners, ids, _ = aruco.detectMarkers(gray, self.aruco_dict,
                                              parameters=self.parameters)
        width, _ = self.resolution
        markers = []
        if np.all(ids != None):
            for i in range(len(corners)):
                x = int(corners[i].mean(axis=1)[0][0])
                y = int(corners[i].mean(axis=1)[0][1])
                marker = {}
                marker["id"] = ids[i]
                marker["corners"] = corners[i]
                marker["distanceToMarker"] = round(depth[y, x] / 1000, 2)
                marker["angleToMarker"] = round((x - (width / 2)) \
                                          * (self.fov / width), 2)
                markers.append(marker)
        draw_markers(rgb, markers, corners)
        if show:
            cv2.imshow("tracker", rgb)
        return rgb, markers
