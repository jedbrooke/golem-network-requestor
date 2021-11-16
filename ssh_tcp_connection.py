import subprocess
import fcntl
import base64
import os
import time
import socket
import binascii
import shlex
import sys

def handle_http_packet(data: bytes):
    request_string = data.decode('utf-8')
    lines = request_string.splitlines()
    request = lines[0]
    host = [l for l in lines if l.startswith("Host: ")][0]
    host = host.split(": ")[1].split(":")[0]
    verb,address,version = request.split(' ')
    if address.startswith("http://"):
        address = address[7:]
    elif address.startswith("https://"):
        address = address[8:]
    print(host)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 80
    if ":" in address:
        address,port = address.split(":")
        port = int(port)
    print(port)
    s.connect((host, port))
    s.sendall(data)
    response = s.recv(1500)
    print(response.decode("ASCII"))
    print("---------")
    return response

def main(cmd: str):
    p = subprocess.Popen(shlex.split(cmd),shell=False,stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    # set stdout reads to non-blocking
    fd = p.stdout.fileno()
    flag = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)
    flag = fcntl.fcntl(fd, fcntl.F_GETFL)

    PROC = p

    first_read = True
    while p.poll() is None:
        data = p.stdout.read()
        if data != None and len(data) > 0:
            if first_read:
                print("disable echo")
                p.stdin.write("stty -echo".encode("ASCII"))
                p.stdin.write('\n'.encode("ASCII"))

                print("create a test file")
                p.stdin.write("touch /root/hello.txt".encode("ASCII"))
                p.stdin.write('\n'.encode("ASCII"))

                print("start proxy server")
                p.stdin.write("/usr/bin/python3 /proxy_server.py".encode('ASCII'))
                p.stdin.write('\n'.encode("ASCII"))
                p.stdin.flush()
                first_read = False
            else:
                try:
                    as_str = data.decode("ASCII").strip().lstrip()
                    print("as_str\n",as_str)
                    print("---------")
                    print(base64.urlsafe_b64decode(as_str).decode('ASCII'))
                    response = handle_http_packet(base64.urlsafe_b64decode(as_str))
                    
                    p.stdin.write(base64.urlsafe_b64encode(response))
                    p.stdin.write('\n'.encode("ASCII"))
                    p.stdin.flush()
                except UnicodeDecodeError:
                    print("unicode decode error")
                except binascii.Error:
                    print("failed to decode")
                    print(data.decode())
            # p.stdin.write(response)
            # p.stdin.flush()
        time.sleep(0.001)
    

if __name__ == '__main__':
    if len(sys.argv) > 1:
        ssh_cmd = base64.urlsafe_b64decode(sys.argv[1]).decode()
        print(ssh_cmd)
        main(ssh_cmd)
    else:
        main('ssh localhost')

