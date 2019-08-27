from helpers import *

HOST = "localhost"
PORT = 8998

#Assuming data sent is in the form of distance,angle

data = {"marker":(2),"distanceToMarker":(4),"angleToMarker":(60), "objectsDetected":("PERSON"),"distanceToObject":(2),"angletoObject":(20)}
# data = {"action":("scanning") ,"objectsDetected":("THREAT"),"distanceToObject":(200),"angletoObject":(20)}
# data = {"action":("scanning") ,"objectsDetected":("PERSON"),"distanceToObject":(2),"angletoObject":(20)}
#Note:
# objectsDetected can be "SUSPECT", "THREAT" or "PERSON"
# action can be either "scanning" or "moving"
# distance and angle are all given by the intel realsense camera

connect_and_send(data,HOST,PORT)


# server =  socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# server.bind(("localhost",8998))
# server.listen()
# while True:
#     connection, address = server.accept()
#     connection.sendall(pickle.dumps(data))
#     connection.close()