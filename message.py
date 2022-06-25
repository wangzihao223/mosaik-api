import struct
import json

class Message():
    def __init__(self, id, type, content):
        self.id = id
        self.type = type
        self.content = content


def get_msg_length(head):
    res = struct.unpack(">I", head)
    return res[0]


def get_payload(fd, length):
    payload = fd.recv(length)
    payload_dic = json.loads(payload.encode())
    msg = Message(payload_dic[1], payload_dic[0],
                    payload_dic[2])
    return msg
