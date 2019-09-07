# Library
from socket import *

class Client:
    def __init__(self):
        print("Bem-vindo ao cliente")
        self.running = True
        self.is_connected = False
        self.client_session = None

    def connect(self, serverName, serverPort = 2121):
        # Connect
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((serverName,serverPort))
        self.client_session = clientSocket
        self.is_connected = True

    
    def start(self):
        running = True
        # Processa input
        while running:
            if self.is_connected:
                text = input()
                command = text.split(' ')[0]
                self.client_session.send(text.encode())
                response = self.client_session.recv(1024)
                print (response.decode(), end= '')
                if command == "quit":
                    self.close()
                    running = False
                elif command == "close":
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