import subprocess
import fcntl
import base64
import os
import time
import socket
import binascii
import shlex
import sys

import struct
from socketserver import ThreadingMixIn, TCPServer, StreamRequestHandler
import threading
from util import *
import pickle



def handle_http_packet(*args):
    p, data = args
    request_string = data.decode('ASCII',errors='ignore')
    print(request_string)
    lines = request_string.splitlines()
    request = lines[0] 
    host = [l for l in lines if l.startswith("Host: ")][0]
    host = host.split(": ")[1].split(":")[0]
    verb,address,version = request.split(' ')
    if address.startswith("http://"):
        address = address[7:]
    elif address.startswith("https://"):
        address = address[8:]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 80
    if ":" in address:
        address,port = address.split(":")
        port = int(port)
    s.connect((host, port))
    s.sendall(data)
    
    first_response = True
    while True:
        response = s.recv(1500)
        packet = Packet(Protocol.HTTP,response)
        p.stdin.write(base64.urlsafe_b64encode(pickle.dumps(packet)))
        p.stdin.write('\n'.encode('ASCII'))
        p.stdin.flush()
        print("read",len(response),"bytes")
        if len(response) < 1 or (first_response and len(response) < 1400):
            break
        first_response = False
    packet = Packet(Protocol.CONTROL,'die')
    print("send die")
    p.stdin.write(base64.urlsafe_b64encode(pickle.dumps(packet)))
    p.stdin.write('\n'.encode('ASCII'))
    p.stdin.flush()

def main(cmd: str,proxy_server_path="/proxy_server.py"):
    
    p = subprocess.Popen(shlex.split(cmd),shell=False,stdin=subprocess.PIPE, stdout=subprocess.PIPE,stderr=sys.stderr)

    # set stdout reads to non-blocking
    fd = p.stdout.fileno()
    flag = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)

    finished_setup = False
    while not finished_setup:
        try:
            data = p.stdout.read()
            if data != None and len(data) > 0:
                # print("disable echo")
                p.stdin.write("stty -echo".encode("ASCII"))
                p.stdin.write('\n'.encode("ASCII"))

                print("start proxy server")
                p.stdin.write(f"/usr/bin/python3 {proxy_server_path}".encode('ASCII'))
                p.stdin.write('\n'.encode("ASCII"))
                p.stdin.flush()
                finished_setup = True
        except TypeError as te:
            pass
        time.sleep(0.001)

    # reset flags to blocking
    fcntl.fcntl(fd, fcntl.F_SETFL, flag)


    while p.poll() is None:
        try:
            data = p.stdout.readline().decode("ASCII")
            packet: Packet = pickle.loads(base64.urlsafe_b64decode(data))
            print("Recived:",packet)
            if packet.protocol == Protocol.HTTP:
                threading.Thread(target=handle_http_packet,args=(p,packet.data,)).start()
            if packet.protocol == Protocol.CONTROL:
                print(packet.data)
        except (pickle.UnpicklingError,EOFError,binascii.Error):
            print(data)
        except KeyboardInterrupt:
            p.kill()

if __name__ == '__main__':
    if len(sys.argv) > 2:
        ssh_cmd = base64.urlsafe_b64decode(sys.argv[1]).decode()
        print(ssh_cmd)
        main(ssh_cmd)
    else:
        main('ssh -tt localhost',"/home/jedbrooke/source/golem-network-requestor/proxy_server.py")

