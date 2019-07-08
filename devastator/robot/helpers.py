import configparser
import pickle

def recv_obj(s):
    packets = []
    while True:
        packet = s.recv(1024)
        if not packet:
            break
        packets.append(packet)
    obj = pickle.loads(b"".join(packets))
    return obj


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