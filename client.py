# Library
from socket import *
import os

class Client:
    def __init__(self):
        print("Bem-vindo ao cliente")
        self.running = True
        self.is_connected = False
        self.client_session = None

    def connect(self, serverName, serverPort = 2121):
        # Connect
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
        clientSocket.connect((serverName,serverPort))
        self.client_session = clientSocket
        self.is_connected = True

    
    def start(self):
        running = True
        # Processa input
        while running:
            if self.is_connected:
                text = input()
                command = text.split(' ')
                self.client_session.send(text.encode())
                if command[0] == "get":
                    response = self.client_session.recv(1024)
                    if response.decode() == "OK":
                        abort = False
                        if os.path.isfile(command[1]):
                            res = input("Deseja sobrescrever o arquivo existente?(y/n)\n")
                            if res != "y":
                                abort = True
                        if abort:
                            self.client_session.send("ABORT".encode())
                        else:
                            self.client_session.send("SIZE".encode())
                            response = self.client_session.recv(1024)
                            self.client_session.send("FILE".encode())
                            packets = int(response.decode())
                            file_transfer = open(command[1], 'wb')
                            for _ in range(packets):
                                data = self.client_session.recv(1024)
                                file_transfer.write(data)
                            file_transfer.close()
                            self.client_session.send("FIN".encode())
                if command[0] == "put":
                    finish = False
                    if not os.path.isfile(command[1]):
                        self.client_session.send("NOT_FOUND".encode())
                    else:
                        self.client_session.send("FOUND".encode())
                        if self.client_session.recv(1024).decode() == "HAVE_EQUAL":
                            if input("Deseja sobrescrever o arquivo?(y/n)") != "y":
                                self.client_session.send("ABORT".encode())
                                finish = True
                            else:
                                self.client_session.send("OK".encode())
                        else:
                            self.client_session.send("OK".encode())
                        if not finish:
                            self.client_session.recv(1024)
                            file_tranfer = open(command[1],'rb')
                            size = os.path.getsize(command[1])
                            packets = int(size/1024)
                            if size%1024!=0:
                                packets += 1
                            self.client_session.send(str(packets).encode())
                            self.client_session.recv(1024)
                            for _ in range(packets):
                                part_file = file_tranfer.read(1024)
                                self.client_session.send(part_file)
                            file_tranfer.close()
                response = self.client_session.recv(1024)
                print (response.decode(), end= '')
                if command[0] == "quit":
                    self.close()
                    running = False
                elif command[0] == "close":
                    self.close()                    
            else:
                text = input(">>> ")
                command = text.split(' ')[0]
                if command == "open":
                    self.connect(serverName = "0.0.0.0")
                    response = self.client_session.recv(1024)
                    print (response.decode(), end= '')
                elif command == "quit":
                    running = False
                else:
                    self.invalido()
    
    def close(self):
        self.client_session.close()
        self.is_connected = False
        
    def invalido(self):
        print("comando invalido")

if __name__ == "__main__":
    Client().start()