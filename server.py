from socket import *
import threading


class Server:
    def __init__(self, serverPort = 2121):
        self.serverSocket = socket(AF_INET,SOCK_STREAM)
        self.serverSocket.bind(('',serverPort))
        self.serverSocket.listen(1)
        print("Servidor ativado com sucesso")
    
    def autentication(self,conn,addr):
        conn.send("login:".encode())
        while True:
            user = conn.recv(1024).decode()
            conn.send("password:".encode())
            password = conn.recv(1024).decode()

            if user == "joao" and password == "123456":
                conn.send("Login realizado com sucesso\n".encode())
                self.client_listen(conn, addr)
                break
            conn.send("credenciais erradas, tente novamente\nlogin:".encode())

    def client_listen(self, conn, addr):
        running = True
        while running:
            text = conn.recv(1024).decode()
            command = text.split(' ')[0]
            if command == "close" or command == "quit":
                running = False
            elif command == "ls":
                conn.send("listando".encode())
            else:
                conn.send("comando invalido\n".encode())
                
        conn.close()
        print(addr, "finalizou a conexao")

    def start(self):
        while True:
            connectionSocket, addr = self.serverSocket.accept()
            print(addr, "conectou-se")
            threading.Thread(target=self.autentication, args=(connectionSocket,addr,)).start()



if __name__ == "__main__":
    Server().start()