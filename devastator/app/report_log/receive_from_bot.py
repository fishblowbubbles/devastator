import json
import socket, pickle
from devastator.app.Facerecognition.Call_Face_Rec import load_known, guess_who, frametest

#ROBOT TO SEND report logs TO PORT 8888
HOST = "192.168.1.136"
# HOST = "192.168.1.185"
PORT = 8888
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
                # print(curr_data)

                enc, names = load_known()
                # print(guess_who(None, enc, names))
                for key in data:
                    data[key]['Persons_Detected'] = "Person Detected: <p/>"
                    for i in  data[key]['Persons_Detected']:
                        person = guess_who(i, enc, names)
                        add_person_to_list = str(person) + " <p/>"
                        data[key]['Persons_Detected'] += add_person_to_list

                    #for testins --------------------------------------------------
                    # person = guess_who(None, enc, names)
                    # data[key]['Persons_Detected'] = "Person Detected: <p/>" + str(person)
                    #--------------------------------------------------------------
                    for i in data[key]['Guns_Detected']:
                        ### gun classification algo
                        data[key]['Guns_Detected'] = "Guns Detected: <p/>" + "SAR21"

                print(data)

                curr_data['data'].update(data)
                with open('reports.json', 'w') as outfile:
                    json.dump(curr_data, outfile,
                              indent=4)

        finally:
            print("YAS")

if __name__ == '__main__':
    update_data()