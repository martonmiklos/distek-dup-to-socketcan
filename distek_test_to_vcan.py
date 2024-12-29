import socket
import struct

import time
import can


interface = "socketcan"
channel = "vcan0"


MCAST_GRP = "239.0.0.222"
MCAST_PORT = 25000
IS_ALL_GROUPS = True


bus = can.Bus(channel=channel, interface=interface)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
if IS_ALL_GROUPS:
    # on this port, receives ALL multicast groups
    sock.bind(("", MCAST_PORT))
else:
    # on this port, listen ONLY to MCAST_GRP
    sock.bind((MCAST_GRP, MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

while True:
    # For Python 3, change next line to "print(sock.recv(10240))"
    udpData = sock.recv(13)
    can_id = (udpData[0] << 24) + (udpData[1] << 16) + (udpData[2] << 8) + udpData[3]
    data = []
    for i in range(udpData[4]):
        data.append(udpData[i + 5])
    msg = can.Message(arbitration_id=can_id, data=data, is_extended_id=True)
    bus.send(msg)
    print("%X - %d %s" % (can_id, len(data), data))

    message = bus.recv(0)
    if message is not None:
        outArr = []
        outArr.append((message.arbitration_id >> 24) & 0xFF)
        outArr.append((message.arbitration_id >> 16) & 0xFF)
        outArr.append((message.arbitration_id >> 8) & 0xFF)
        outArr.append((message.arbitration_id >> 0) & 0xFF)
        outArr.append(message.dlc)
        for i in range(message.dlc):
            outArr.append(message.data[i])
        print(bytes(outArr))
        sock.sendto(bytes(outArr), (MCAST_GRP, MCAST_PORT))
