import glob

import cv2
import cv2.aruco as aruco
import numpy as np

from robot import realsense
from robot.helpers import get_data
from vision.helpers import split_rgbd


class Tracker:
    def __init__(self):
        self.aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
        self.parameters = aruco.DetectorParameters_create()
        self.parameters.adaptiveThreshConstant = 10

    def detect(self, rgb, depth, resolution=realsense.RESOLUTION,
               fov=realsense.FOV, show=False):
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        corners, ids, _ = aruco.detectMarkers(gray, self.aruco_dict,
                                              parameters=self.parameters)
        width, _ = resolution
        markers = []

        if np.all(ids != None):
            for i in range(len(corners)):
                x = int(corners[i].mean(axis=1)[0][0])
                y = int(corners[i].mean(axis=1)[0][1])
                marker = {}
                marker["id"] = ids[i]
                marker["corners"] = corners[i]
                marker["distance"] = round(depth[y, x] / 1000, 2)
                marker["angle"] = round((x - (width / 2)) * (fov / width), 2)
                markers.append(marker)

        aruco.drawDetectedMarkers(rgb, corners)
        if show:
            cv2.imshow("tracker", rgb)

        return rgb, markers
