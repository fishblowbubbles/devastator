import pickle

def recv_obj(socket):
    packets = []
    while True:
        packet = socket.recv(1024)
        if not packet:
            break
        packets.append(packet)
    obj = pickle.loads(b"".join(packets))
    return obj