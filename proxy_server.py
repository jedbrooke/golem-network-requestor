import socket
import threading
import base64


HOST = "0.0.0.0"
PORT = 4242
REMOTE_HOST = "localhost"
REMOTE_PORT = 4243


# https://www.geeksforgeeks.org/creating-a-proxy-webserver-in-python-set-1/
def start_server():
    socketServer = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    socketServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socketServer.bind((HOST,PORT))
    socketServer.listen()
    serving_clients = True

    while serving_clients:
        try:
            conn,addr = socketServer.accept()
            threading.Thread(target=handle_client,args=(conn,addr)).start()
        except KeyboardInterrupt:
            serving_clients = False


def handle_client(*args):
    conn, addr = args

    data = conn.recv(1500)
    print(base64.urlsafe_b64encode(data).decode("ASCII"),flush=True)
    data = input()
    if data != None and len(data) > 0:
        data = base64.urlsafe_b64decode(data)
        conn.send(data)
    

if __name__ == '__main__':
    start_server()
