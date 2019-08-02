# import pygame
# import socket
# from pygame_functions import *
# from helpers import *
#
# #
# # pygame.init()
# HOST = "localhost"
# PORT = 8998
#
# #####################################################################
# curr_x = 0.0
# curr_y = 0.0
#
# # # #note:
# # # #Marker 1 is at position (50,740) on map
# # # #Marker 2 is at position (55,210) on map
# # # #Mmarker 3 is at position (715,210) on map
# # # #Marker 4 is at position (670, 40) on map
# # # #Marker 5 is at position (825,460) on map
# # # #Marker 6 is at position (600,665) on map
#
# def init_pos (robot):
#     global curr_x
#     global curr_y
#
#     moveSprite(robot, 50, 740, True) #init position of robot
#     curr_x = 50
#     curr_y = 740
#
# def calculate_position(robot,information):
#     global curr_x
#     global curr_y
#
#     if str(information["marker"]) =="1":
#         angle_val = information["angleToMarker"]
#         angle_radians = float(angle_val)*(math.pi/180.0)
#         distance_in_metres = information["distanceToMarker"]
#         distance =  distance_in_metres * (720.0/3.87)
#         new_x = 50 + float(distance)*math.sin(angle_radians)
#         new_y = 740 + float(distance)*math.cos(angle_radians)
#         curr_x = new_x
#         curr_y  = new_y
#         pause(600)
#         moveSprite(robot,new_x,new_y,True)
#
#     elif str(information["marker"]) =="2":
#         angle_val = information["angleToMarker"]
#         angle_radians = float(angle_val)*(math.pi/180.0)
#         distance_in_metres = information["distanceToMarker"]
#         distance =  distance_in_metres * (720.0/3.87)
#         new_x = 55 + float(distance)*math.sin(angle_radians)
#         new_y = 210 + float(distance)*math.cos(angle_radians)
#         curr_x = new_x
#         curr_y  = new_y
#         pause(600)
#         moveSprite(robot,new_x,new_y,True)
#
#     elif str(information["marker"]) =="3":
#         angle_val = information["angleToMarker"]
#         angle_radians = float(angle_val)*(math.pi/180.0)
#         distance_in_metres = information["distanceToMarker"]
#         distance =  distance_in_metres * (720.0/3.87)
#         new_x = 715 + float(distance)*math.sin(angle_radians)
#         new_y = 210 + float(distance)*math.cos(angle_radians)
#         curr_x = new_x
#         curr_y  = new_y
#         pause(600)
#         moveSprite(robot,new_x,new_y,True)
#
#     elif str(information["marker"]) =="4":
#         angle_val = information["angleToMarker"]
#         angle_radians = float(angle_val)*(math.pi/180.0)
#         distance_in_metres = information["distanceToMarker"]
#         distance =  distance_in_metres * (720.0/3.87)
#         new_x = 670 + float(distance)*math.sin(angle_radians)
#         new_y = 40 + float(distance)*math.cos(angle_radians)
#         curr_x = new_x
#         curr_y  = new_y
#         pause(600)
#         moveSprite(robot,new_x,new_y,True)
#
#     # elif str(information["marker"]) =="5":
#     #     angle_val = information["angleToMarker"]
#     #     angle_radians = float(angle_val)*(math.pi/180.0)
#     #     distance_in_metres = information["distanceToMarker"]
#     #     distance =  distance_in_metres * (720.0/3.87)
#     #     new_x = 825 + float(distance)*math.sin(angle_radians)
#     #     new_y = 460 + float(distance)*math.cos(angle_radians)
#     #     curr_x = new_x
#     #     curr_y  = new_y
#     #     pause(600)
#     #     moveSprite(robot,new_x,new_y,True)
#     #
#     # elif str(information["marker"]) =="6":
#     #     angle_val = information["angleToMarker"]
#     #     angle_radians = float(angle_val)*(math.pi/180.0)
#     #     distance_in_metres = information["distanceToMarker"]
#     #     distance =  distance_in_metres * (720.0/3.87)
#     #     new_x = 600 + float(distance)*math.sin(angle_radians)
#     #     new_y = 665 + float(distance)*math.cos(angle_radians)
#     #     curr_x = new_x
#     #     curr_y  = new_y
#     #     pause(600)
#     #     moveSprite(robot,new_x,new_y,True)
#
# def place_marker(information):
#     if information["objectsDetected"] == "SUSPECT":
#         marker = makeSprite("suspect_marker.png")
#
#     elif information["objectsDetected"] == "PERSON":
#         marker = makeSprite("person_marker.png")
#
#     elif information["objectsDetected"] == "THREAT":
#         marker = makeSprite("threat_marker.png")
#
#     distance_in_metres = information["distanceToObject"]
#     distance = distance_in_metres * (720.0 / 3.87)
#     angle_val = information["angletoObject"]
#     angle_radians = float(angle_val)*(math.pi/180.0)
#     marker_x = curr_x - float(distance)* math.sin(angle_radians)
#     marker_y = curr_y - float(distance) * math.cos(angle_radians)
#     pause(600)
#     moveSprite(marker,marker_x,marker_y)
#     showSprite(marker)
#
#
#
# ##########################################################################3
# #main func
#
# def run():
#     pygame.init()
#     screenSize(874, 800, -6, -20)
#     setBackgroundImage("map w markers.jpg")
#     robot = makeSprite("Wendi.png")
#     # label = makeLabel("OVERRIDE", 60, 440, 720, "#ba1818",
#     #                   "sitkasmallsitkatextsitkasubheadingsitkaheadingsitkadisplaysitkabanner", "#ff5757")
#     # showLabel(label)
#     showSprite(robot)
#     init_pos(robot)
#
#
#     with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as server:
#         server.bind((HOST,PORT))
#         server.listen()
#         # buttonClicked(override_button)
#
#         try:
#             while True:
#                 # mouse = pygame.mouse.get_pos()
#                 # print(mouse)
#                 # event = pygame.event.get()
#                 connection, _ = server.accept()
#                 data = recv_obj(connection)
#                 # print(data)
#                 if data["action"]== "moving":
#                     calculate_position(robot,data)
#                 elif data["action"] == "scanning":
#                     scan_label = makeLabel("Scanning...",30,curr_x+40,curr_y-15)
#                     showLabel(scan_label)
#                     # scan_label = makeTextBox(curr_x+30,curr_y-30,200,0,"Scanning...")
#                     # showTextBox(scan_label)
#                     place_marker(data)
#                     pause(500)
#                     hideLabel(scan_label)
#
#                 # endWait()
#
#                 # buttonClicked(override_button)
#                 # for event in pygame.event.get():
#                 #     if event.type == pygame.QUIT:
#                 #         connection.close()
#                 #         pygame.quit()
#                 #         quit()
#                 # for event in pygame.event.get():
#                 #     if event.type == pygame.MOUSEBUTTONDOWN:
#                 #         #Set the x,y positions of the mouse click
#                 #         mous= event.pos
#                 #         print(x,y)
#                 #         if override_button.get_rect().collidepoint(x,y):
#                 #             print('clicked on button')
#
#         finally:
#             connection.close()
#             sys.exit(0)
#
#
# run()