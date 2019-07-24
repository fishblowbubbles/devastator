import configparser
import pickle
import socket
import time


def recv_obj(connection):
    packets = []
    while True:
        packet = connection.recv(1024)
        if not packet:
            break
        packets.append(packet)
    obj = pickle.loads(b"".join(packets))
    return obj


def get_data(host, port):
    with socket.socket() as client:
        client.connect((host, port))
        data = recv_obj(client)
    return data


def send_data(connection, data):
    try:
        connection.sendall(pickle.dumps(data))
        connection.shutdown(socket.SHUT_RDWR)
    except ConnectionResetError:
        print("A connection was reset ...")
    except BrokenPipeError:
        print("A pipe broke ...")


def connect_and_send(data, host, port):
    with socket.socket() as client:
        try:
            client.connect((host, port))
            send_data(client, data)
        except ConnectionRefusedError:
            print("The connection was refused ...")


class ConfigFile:
    def __init__(self, path):
        self.config = configparser.ConfigParser()
        self.config.read(path)
        self.path = path

    def get(self, section, key):
        value = self.config[section][key]
        return value

    def save(self, section, key, value):
        self.config[section][key] = str(value)
        with open(self.path, "w") as file:
            self.config.write(file)
