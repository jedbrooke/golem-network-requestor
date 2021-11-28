import subprocess
import fcntl
import base64
import os
import time
import socket
import binascii
import shlex
import sys

# for socks5 proxy later
# from socketserver import ThreadingMixIn, TCPServer, StreamRequestHandler
import threading
from util import *
import pickle
import logging

# I made my own logging class so it doesn't interfere with the logging from yagna
class Log():
    def __init__(self,path,level=logging.WARNING):
        self.path = path
        self.level = level
        with open(path,"w"):
            pass
    
    def info(self, msg: str):
        if self.level >= logging.INFO:
            self.write(msg)

    def debug(self, msg: str):
        if self.level >= logging.DEBUG:
            self.write(msg)

    def warning(self, msg: str):
        if self.level >= logging.WARNING:
            self.write(msg)

    def error(self, msg: str):
        if self.level >= logging.ERROR:
            self.write(msg)

    def write(self,msg):
        with open(self.path,"a") as fp:
                fp.write(msg)
                fp.write("\n")

logger = Log("output/ssh_connection.log")


def handle_http_packet(*args):
    p: subprocess.Popen = None
    data: bytes = None
    p, data = args

    request_string = data.decode('ASCII',errors='ignore')
    logger.debug(request_string)
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
        logger.debug(f"read {len(response)} bytes")
        if len(response) < 1 or (first_response and len(response) < 1400):
            break
        first_response = False
    packet = Packet(Protocol.CONTROL,'die')
    logger.debug("send die")
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
                # logger.debug("disable echo")
                p.stdin.write("stty -echo".encode("ASCII"))
                p.stdin.write('\n'.encode("ASCII"))

                logger.debug("start proxy server")
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
            logger.debug(f"Recived: {packet}")
            if packet.protocol == Protocol.HTTP:
                threading.Thread(target=handle_http_packet,args=(p,packet.data,)).start()
            if packet.protocol == Protocol.CONTROL:
                logger.debug(str(packet.data))
        except (pickle.UnpicklingError,EOFError,binascii.Error):
            logger.debug(data)
        except KeyboardInterrupt:
            p.kill()

if __name__ == '__main__':
    if len(sys.argv) > 2:
        ssh_cmd = base64.urlsafe_b64decode(sys.argv[1]).decode()
        logger.debug(ssh_cmd)
        main(ssh_cmd)
    else:
        main('ssh -tt localhost',"/home/jedbrooke/source/golem-network-requestor/proxy_server.py")

