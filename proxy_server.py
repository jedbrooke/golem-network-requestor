import socket
import threading
import base64
import sys
from queue import Queue
import pickle
from util import *


HOST = "0.0.0.0"
PORT = 4242

class Connection():
    def __init__(self,conn: socket.socket,addr, write_queue: Queue,read_queue: Queue):
        self.conn = conn
        self.addr = addr
        self.write_queue = write_queue
        self.read_queue = read_queue

# https://www.geeksforgeeks.org/creating-a-proxy-webserver-in-python-set-1/
def start_server():
    socketServer = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    socketServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socketServer.bind((HOST,PORT))
    socketServer.listen()
    serving_clients = True
    
    write_queue = Queue()
    read_queue = Queue()

    # start write Queue
    threading.Thread(target=handle_write_queue,args=(write_queue,)).start()
    
    # start read Queue
    threading.Thread(target=handle_read_queue,args=(read_queue,)).start()
    print()
    while serving_clients:
        try:
            conn,addr = socketServer.accept()
            c = Connection(conn,addr,write_queue,read_queue)
            handle_client(c)
        except KeyboardInterrupt:
            serving_clients = False


def handle_write_queue(write_queue: Queue):
    while True:
        packet: Packet = write_queue.get()
        print(base64.urlsafe_b64encode(pickle.dumps(packet)).decode("ASCII"),flush=True)

def handle_read_queue(packet_queue: Queue):
    while True:
        data = input()
        packet: Packet = pickle.loads(base64.urlsafe_b64decode(data))
        packet_queue.put(packet)


def handle_client(connection: Connection):
    data = connection.conn.recv(4096)
    if is_http_packet(data.decode()):
        connection.write_queue.put(Packet(Protocol.HTTP,data))
    else:
        connection.write_queue.put(Packet(Protocol.CONTROL,data))
    while True:
        response_packet: Packet = connection.read_queue.get()
        if response_packet.protocol == Protocol.CONTROL:
            break
        else:
            connection.conn.sendall(response_packet.data)
    connection.write_queue.put(Packet(Protocol.CONTROL,"client disconnect"))
    connection.conn.close()

if __name__ == '__main__':
    start_server()
