import cv2
import cv2.aruco as aruco
import numpy as np

from robot import realsense
from robot.helpers import get_data
from vision.helpers import draw_markers, split_rgbd

MARKER_LENGTH = 15.5    # cm
FOCAL_LENGTH  = 9.14715 # cm


class Tracker:
    def __init__(self, resolution=realsense.RESOLUTION, 
                 fov=realsense.FOV, focal_length=FOCAL_LENGTH):
        self.resolution, self.fov = resolution, fov
        self.aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
        self.parameters = aruco.DetectorParameters_create()
        self.parameters.adaptiveThreshConstant = 10
        self.focal_length = focal_length

    def _get_side_length(self, corners):
        sides_list = []
        for i in range(len(corners[0]) - 1, -1, -1):
            corner1 = corners[0][i - 1]
            corner2 = corners[0][i]
            distance = np.linalg.norm(corner1 - corner2)
            sides_list.append(distance)
        side_length = sum(sides_list) / len(sides_list)
        return side_length

    def _get_focal_length(self, corners, distance, marker_length=MARKER_LENGTH):
        side_length = self._get_side_length(corners)
        focal_length = side_length * distance / marker_length
        return focal_length

    def _get_depth(self, corners, marker_length=MARKER_LENGTH):
        depth = marker_length * self.focal_length / self._get_side_length(corners)
        return depth

    def _get_markers(self, rgb):
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        corners, ids, _ = aruco.detectMarkers(gray, self.aruco_dict, parameters=self.parameters)
        return corners, ids

    def calibrate(self, rgb, distance):
        corners, ids = self._get_markers(rgb)
        markers = []
        if np.all(ids != None):
            for i in range(len(corners)):
                focal_length = self._get_focal_length(corners[i], distance)
        draw_markers(rgb, markers, corners)
        return rgb, focal_length

    def detect(self, rgb, depth):
        corners, ids = self._get_markers(rgb)
        width, _ = self.resolution
        markers = []
        if np.all(ids != None):
            for i in range(len(corners)):
                x = int(corners[i].mean(axis=1)[0][0])
                marker = {}
                marker["id"] = ids[i][0]
                marker["corners"] = corners[i]
                marker["distanceToMarker"] = self._get_depth(corners[i])
                marker["angleToMarker"] = round((x - (width / 2)) \
                                          * (self.fov / width), 2)
                marker["objectsDetected"] = []
                markers.append(marker)
        draw_markers(rgb, markers, corners)
        return rgb, markers
