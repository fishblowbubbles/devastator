import pygame
import socket
from devastator.app.map_app.pygame_functions import *
from devastator.app.map_app.helpers import *

HOST = "192.168.1.136"
# HOST = "localhost"
PORT = 8998

curr_x = 0.0
curr_y = 0.0

# # #note:
# # #Marker 1 is at position (50,740) on map
# # #Marker 2 is at position (55,210) on map
# # #Mmarker 3 is at position (715,210) on map
# # #Marker 4 is at position (670, 40) on map
# # #Marker 5 is at position (825,460) on map
# # #Marker 6 is at position (600,6


class Robot():
    def __init__(self, robot_direction, robot_x, robot_y):
        self.robot_direction = robot_direction
        self.robot_x = robot_x
        self.robot_y = robot_y
        self.sprite = makeSprite("Wendi.png")
        moveSprite(self.sprite, 50, 740, True)
        showSprite(self.sprite)

    def get_xy(self):
        return self.robot_x, self.robot_y

    def set_xy(self, Robotdirection, newx, newy):
        self.robot_direction = Robotdirection
        self.robot_x = int((1/8)*newx + (7/8)*self.robot_x)
        self.robot_y = int((1/8)*newy + (7/8)*self.robot_y)
        pause(10)
        moveSprite(self.sprite, self.robot_x, self.robot_y, True)
        showSprite(self.sprite)

    def detected_person(self, information):
        marker = makeSprite("person_marker.png")
        for i in range(len(information["objectsDetected"])):
                # print(information["objectsDetected"][i])
            if information["objectsDetected"][i] == "SUSPECT":
                marker = makeSprite("suspect_marker.png")

            elif information["objectsDetected"][i] == "PERSON":
                marker = makeSprite("person_marker.png")

            elif information["objectsDetected"][i] == "THREAT":
                marker = makeSprite("threat_marker.png")

            distance_from_person = information["distanceToObject"][i]
            # print(distance_from_person)
            angle_from_person = information["angleToObject"][i]
            marker_x, marker_y = self.get_person_coord(distance_from_person, angle_from_person)
            pause(800)
            moveSprite(marker, marker_x, marker_y)
            showSprite(marker)

    def get_person_coord(self, distance_from_person, angle_from_person):
        person_x_coord = 0.0
        person_y_coord = 0.0
        distance = distance_from_person * (720.0 / (3.87))
        angle = float(angle_from_person) * (math.pi / 180.0)

        if self.robot_direction == "down":
            person_x_coord = self.robot_x + distance * math.sin(angle)
            person_y_coord = self.robot_y + distance * math.cos(angle)

        elif self.robot_direction == "up":
            person_x_coord = -1.0 * distance * math.sin(angle) + self.robot_x
            person_y_coord = self.robot_y - distance * math.cos(angle)

        elif self.robot_direction == "right":
            person_y_coord = -1.0 * distance * math.sin(angle) + self.robot_y
            person_x_coord = self.robot_x + distance * math.cos(angle)

        elif self.robot_direction == "left":
            person_y_coord = distance * math.sin(angle) + self.robot_y
            person_x_coord = self.robot_x - distance * math.cos(angle)

        return person_x_coord, person_y_coord


class ArucoMarker():
    def __init__(self, marker_direction, id, marker_x_coord, marker_y_coord):
        self.id = id
        self.marker_direction = marker_direction
        self.marker_x_coord = marker_x_coord
        self.marker_y_coord = marker_y_coord

    def set_robot_coord(self, Robot, distance_from_marker):
        distance = distance_from_marker * (720.0 / (3.87))  # converted distance

        if self.marker_direction == "up":
            new_y = self.marker_y_coord - distance
            new_x = self.marker_x_coord
            Robot.set_xy("down", new_x, new_y)

        elif self.marker_direction == "down":
            new_y = self.marker_y_coord + distance
            new_x = self.marker_x_coord
            Robot.set_xy("up", new_x, new_y)

        elif self.marker_direction == "left":
            new_y = self.marker_y_coord
            new_x = self.marker_x_coord - distance
            Robot.set_xy("right", new_x, new_y)

        elif self.marker_direction == "right":
            new_y = self.marker_y_coord
            new_x = self.marker_x_coord + distance
            Robot.set_xy("left", new_x, new_y)


def run():
    pygame.init()
    screenSize(874, 800, -6, -20)
    setBackgroundImage("map w markers.jpg")
    robot = Robot("up", 50,740)
    marker1 = ArucoMarker("up",1,50,740)
    marker2 = ArucoMarker("down", 2, 55, 210)
    marker3 = ArucoMarker("left", 3, 715, 210)
    marker4 = ArucoMarker("down", 4, 670, 40)
    markers = {1:marker1, 2:marker2, 3:marker3, 4:marker4}

    # label = makeLabel("OVERRIDE", 60, 440, 720, "#ba1818",
    #                   "sitkasmallsitkatextsitkasubheadingsitkaheadingsitkadisplaysitkabanner", "#ff5757")
    # showLabel(label)
      # init position of robot


    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as server:
        server.bind((HOST,PORT))
        server.listen()

        try:
            while True:
                connection, _ = server.accept()
                data = recv_obj(connection)
                print(data)
                markers[data["id"]].set_robot_coord(robot, data["distanceToMarker"])

                if len(data["objectsDetected"]) != 0:
                    robot_curr_x,robot_curr_y = robot.get_xy()
                    scan_label = makeLabel("Scanning...",30,robot_curr_x+40,robot_curr_y-15)
                    showLabel(scan_label)
                    robot.detected_person(data)
                    pause(800)
                    hideLabel(scan_label)

                print("done")

        finally:
            endWait()
            print("here")
            sys.exit(0)

if __name__ == '__main__':
    run()




