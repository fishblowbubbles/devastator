import numpy as np
import sys
sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
import cv2
import cv2.aruco as aruco
import glob
import socket
import pickle
import timeit

def get_frame(input_stream, HOST=None, PORT=None):
    if input_stream == "cam":
        input_stream = 0 
        cap = cv2.VideoCapture(input_stream)
        ret, frame = cap.read()
    elif input_stream == "server":
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((HOST, PORT))
            frame = recv_object(client)
        #RGBD
    else:
        input_stream
        cap = cv2.VideoCapture(input_stream)
        ret, frame = cap.read()
    return frame


def recv_object(client):
    packets = []
    while True:
        packet = client.recv(1024)
        if not packet:
            break
        packets.append(packet)
    object = pickle.loads(b"".join(packets))
    return object




def calibrate():
    ####---------------------- CALIBRATION ---------------------------
    # termination criteria for the iterative algorithm
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    # checkerboard of size (7 x 6) is used
    objp = np.zeros((6*7,3), np.float32)
    objp[:,:2] = np.mgrid[0:7,0:6].T.reshape(-1,2)

    # arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.

    # iterating through all calibration images
    # in the folder
    images = glob.glob('calib_images/*.jpg')

    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

        # find the chess board (calibration pattern) corners
        ret, corners = cv2.findChessboardCorners(gray, (7,6),None)

        # if calibration pattern is found, add object points,
        # image points (after refining them)
        if ret == True:
            objpoints.append(objp)

            # Refine the corners of the detected corners
            corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
            imgpoints.append(corners2)

            # Draw and display the corners
            img = cv2.drawChessboardCorners(img, (7,6), corners2,ret)


    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)

    return ret, mtx, dist, rvecs, tvecs





def get_markers(frame):
###------------------ ARUCO TRACKER ---------------------------
    
    # operations on the frame
    gray = cv2.cvtColor(frame[:, :, :3].astype(np.uint8), cv2.COLOR_RGB2GRAY)
    depth = frame[:, :, 3].astype(np.uint8)

    # set dictionary size depending on the aruco marker selected
    aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)

    # detector parameters can be set here (List of detection parameters[3])
    parameters = aruco.DetectorParameters_create()
    parameters.adaptiveThreshConstant = 10

    # lists of ids and the corners belonging to each id
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    markers = []
    # check if the ids list is not empty
    # if no check is added the code will crash
    if np.all(ids != None):

#-----------------------------Portion includes where the marker is facing etc --------------------------
        # add following params to function if you wanna use ", ret, mtx, dist, rvecs, tvecs "
        # estimate pose of each marker and return the values
        # rvet and tvec-different from camera coefficients
    #   rvec, tvec ,_ = aruco.estimatePoseSingleMarkers(corners, 0.05, mtx, dist)
        #(rvec-tvec).any() # get rid of that nasty numpy value array error
    #    for i in range(0, ids.size):
            # draw axis for the aruco markers
    #        aruco.drawAxis(frame, mtx, dist, rvec[i], tvec[i], 0.1)
#-----------------------------Portion includes where the marker is facing etc --------------------------
        
        
        # horizontal angle that the marker is away from the center line of sight of the robot 
        # value from (-43.5 deg to + 43.5 deg) where 43.5 is left/right?

        
        for i in range(len(corners)):
            marker_details = {}
            center_x = int(corners[i].mean(axis=1)[0][0])
            center_y = int(corners[i].mean(axis=1)[0][1])
            marker_h_angle = round((center_x - 640) * (87/1280),2)
            depth_point = round(depth[center_y, center_x]/1000,2)
            marker_details["angleToMarker"] = marker_h_angle
            marker_details["distanceToMarker"] = depth_point
            marker_details["id"] = ids[i]#[0]
            markers.append(marker_details)
    return markers



def main():
    start = timeit.default_timer()
    HOST = "127.0.0.1"
    PORT = 4445

    frame = get_frame("server", HOST, PORT)
    #calibration not currently required
    #ret, mtx, dist, rvecs, tvecs = calibrate()
    markers = get_markers(frame) #, ret, mtx, dist, rvecs, tvecs)
    print(markers)

if __name__ == '__main__':
    sys.exit(main() or 0)
