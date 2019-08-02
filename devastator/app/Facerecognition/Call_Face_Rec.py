import sys
import timeit
import face_recognition
import cv2
import numpy as np
import math
frametest = np.numarray
def face_distance_to_conf(face_distance, face_match_threshold=0.47):
    if face_distance > face_match_threshold:
        range = (1.0 - face_match_threshold)
        linear_val = (1.0 - face_distance) / (range * 2.0)
        return linear_val
    else:
        range = face_match_threshold
        linear_val = 1.0 - (face_distance / (range * 2.0))
        return linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))

# Get a reference to webcam #0 (the default one)

def load_known():
# Load a sample picture and learn how to recognize it.
    image = face_recognition.load_image_file("./known/ResumePic.jpg")
    face_encoding = face_recognition.face_encodings(image)[0]
    image2 = face_recognition.load_image_file("./known/download.jpg")
    face_encoding2 = face_recognition.face_encodings(image2)[0]
    image3 = face_recognition.load_image_file("./known/amirul.jpg")
    face_encoding3 = face_recognition.face_encodings(image3)[0]
    image4 = face_recognition.load_image_file("./known/martin.jpg")
    face_encoding4 = face_recognition.face_encodings(image4)[0]
    image5 = face_recognition.load_image_file("./known/wesley.jpg")
    face_encoding5 = face_recognition.face_encodings(image5)[0]
    image6 = face_recognition.load_image_file("./known/Wenshu.jpg")
    face_encoding6 = face_recognition.face_encodings(image6)[0]
    image7 = face_recognition.load_image_file("./known/tingyu.jpg")
    face_encoding7 = face_recognition.face_encodings(image7)[0]

# Create arrays of known face encodings and their names
    known_face_encodings = [
    face_encoding,
    face_encoding2,
    face_encoding3,
    face_encoding4,
    face_encoding5,
    face_encoding6,
    face_encoding7
    ]
    known_face_names = [
    "Yu Jin",
    "Cheryl",
    "Amirul",
    "Martin",
    "Weseley",
    "Wen Shu",
    "Ting Yu"
    ]
    
    return known_face_encodings, known_face_names

def guess_who(picture,known_face_encodings, known_face_names, thresh = 0.46):
    # video_capture = cv2.VideoCapture("example.png")

    ###for testing
    # video_capture = cv2.VideoCapture(0)
    # ret, frame = video_capture.read()
    # global frametest
    # frametest = frame

    frame = picture #picture is the numpy array sent by robot

    # Grab a single frame of video

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_frame = frame[:, :, ::-1]

    # Find all the faces and face enqcodings in the frame of video
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
    #matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance = 0.46)
    
    name = "Unknown"

    # Or instead, use the known face with the smallest distance to the new face
    confidences = np.zeros(len(known_face_encodings))
    distances = face_recognition.face_distance(known_face_encodings, face_encoding)

    # could be optimized
    for i in range(len(known_face_encodings)):
        confidences[i] = face_distance_to_conf(distances[i], thresh)
    
    print(confidences)
    best_match_index = np.argmax(confidences)
    if confidences[best_match_index] > thresh:
        name = known_face_names[best_match_index]
        return name, confidences[best_match_index]
    return name, -1



enc, names = load_known()
# print(guess_who(None,enc, names))
# print(frametest)

