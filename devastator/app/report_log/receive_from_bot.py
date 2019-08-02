import json
import socket, pickle
#ROBOT TO SEND report logs TO PORT 8886
HOST = "192.168.1.136"
# HOST = "192.168.1.185"
PORT = 8886
data = {}

def recv_obj(s):
    packets = []
    while True:
        packet = s.recv(1024)
        if not packet:
            break
        packets.append(packet)
    obj = pickle.loads(b"".join(packets))
    return obj

def update_data():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()

        try:
            while True:
                connection, _ = server.accept()
                data = recv_obj(connection)
                print(data)
                curr_data = json.load(open('reports.json'))
                print(curr_data)
                curr_data['data'].update(data)
                with open('reports.json', 'w') as outfile:
                    json.dump(curr_data, outfile,
                              indent=4)

        finally:
            print("YAS")

if __name__ == '__main__':
    update_data()