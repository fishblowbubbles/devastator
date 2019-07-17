import sys
sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
import cv2 as cv
import pyrealsense2 as rs
import numpy as np
import timeit


pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
profile = config.resolve(pipeline)
pipeline.start(config)

start = timeit.default_timer()
num_frames = 0

while True:

    frames = pipeline.wait_for_frames()
    color_frame = frames.get_color_frame()
    if not color_frame:
        continue
    original_image = np.array(color_frame.get_data())

    # Convert color image to grayscale for Viola-Jones
    grayscale_image = cv.cvtColor(original_image, cv.COLOR_BGR2GRAY)

    # Load the classifier and create a cascade object for face detection

    face_cascade = cv.CascadeClassifier('./haarcascade_frontalface_alt.xml')

    detected_faces = face_cascade.detectMultiScale(grayscale_image)

    crops = []

    for (column, row, width, height) in detected_faces:
        cv.rectangle(
	    original_image,
	    (column, row),
	    (column + width, row + height),
	    (0, 255, 0),
	    2)
        crops.append(original_image[row: row + height, column: column + width])

    num_frames = num_frames + 1
    cv.imshow('Video', original_image)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

print(num_frames/(timeit.default_timer() - start), "frames per second")
video_capture.release()
cv.destroyAllWindows()

