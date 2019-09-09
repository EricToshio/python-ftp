# Bibliotecas
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
import os

class Client:
    """Classe que representa o cliente"""

    def __init__(self):
        """Construtor do cliente
        Declara as variaveis:
        running: se o cliente esta sendo executado
        is_connected: se o cliente esta conectado a algum servidor
        cliente_session: Socket do cliente que esta conectado
        """
        self.running = False
        self.is_connected = False
        self.client_session = None

    def connect(self, serverName, serverPort = 2121):
        """Conecta o cliente ao servidor desejado"""
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
        clientSocket.connect((serverName,serverPort))
        self.client_session = clientSocket
        self.is_connected = True

    def start(self):
        """Inicializa a execução do cliente"""
        print("Bem-vindo ao cliente")
        self.running = True
        # Enquanto estiver ativo
        while self.running:
            # Caso esteja conectado
            if self.is_connected:
                # le o comando
                text = input()
                command = text.split(' ')
                # envia para o servidor
                self.client_session.send(text.encode())
                # caso seja o comando de get
                if command[0] == "get":
                    self.get_command(command)
                # caso seja o comando de put
                if command[0] == "put":
                    self.put_command(command)
                # resposta do servidor
                print (self.client_session.recv(1024).decode(), end= '')
                # comando quit
                if command[0] == "quit":
                    self.close_connection()
                    self.running = False
                # comando close
                elif command[0] == "close":
                    self.close_connection()
            # Caso nao esteja conectado                 
            else:
                # Cli do cliente
                text = input(">>> ")
                command = text.split(' ')
                # comando open
                if command[0] == "open":
                    if len(command) != 2:
                        print("numero de argumentos incorretos")
                    else:
                        self.connect(serverName = command[1])
                        print (self.client_session.recv(1024).decode(), end= '')
                # comando quit
                elif command[0] == "quit":
                    self.running = False
                # comando invalidos
                else:
                    print("comando invalido")
    
    def close_connection(self):
        """Fecha a conexao com o servidor"""
        self.client_session.close()
        self.is_connected = False
    
    def get_command(self,command):
        """Processo para execução do comando get"""
        # recebeu confirmacao se arquivo existe no servidor
        if self.client_session.recv(1024).decode() == "OK":
            abort = False
            # verifica se o arquivo existe no cliente
            if os.path.isfile(command[1]):
                res = input("Deseja sobrescrever o arquivo existente?(y/n)\n")
                if res != "y":
                    abort = True
            # cancela a acao caso o usuario nao queira sobrescrever
            if abort:
                self.client_session.send("ABORT".encode())
            else:
                # requisita o numero de pacotes necessarios
                self.client_session.send("SIZE".encode())
                packets = int(self.client_session.recv(1024).decode())
                # requisita o arquivo
                self.client_session.send("FILE".encode())
                # recebe todos os pacotes
                file_transfer = open(command[1], 'wb')
                for _ in range(packets):
                    data = self.client_session.recv(1024)
                    file_transfer.write(data)
                file_transfer.close()
                # avisa que terminou de receber o arquivo
                self.client_session.send("FIN".encode())
        else:
            self.client_session.send("ABORT".encode())
    
    def put_command(self,command):
        """Processo para execução do comando put"""
        finish = False
        # Recebe a busca
        self.client_session.recv(1024)
        # verifica se o arquivo existe no cliente
        if not os.path.isfile(command[1]):
            # avisa caso nao tenha encontrado
            self.client_session.send("NOT_FOUND".encode())
        else:
            self.client_session.send("FOUND".encode())
            # recebe a informacao se o arquivo ja existe no diretorio do servidor
            if self.client_session.recv(1024).decode() == "HAVE_EQUAL":
                # pergunta se quer sobrescreve-lo
                if input("Deseja sobrescrever o arquivo?(y/n)") != "y":
                    # cancela a transmissao
                    self.client_session.send("ABORT".encode())
                    finish = True
                else:
                    # avisa que pode continua a transferencia
                    self.client_session.send("OK".encode())
            else:
                # avisa que pode continuar a transferencia
                self.client_session.send("OK".encode())
            if not finish:
                # transferencia
                self.client_session.recv(1024)
                file_tranfer = open(command[1],'rb')
                size = os.path.getsize(command[1])
                packets = int(size/1024)
                if size%1024!=0:
                    packets += 1
                # Envia o numero de pacotes necessarios para transferir o arquivo
                self.client_session.send(str(packets).encode())
                self.client_session.recv(1024)
                # Envia o arquivo
                for _ in range(packets):
                    part_file = file_tranfer.read(1024)
                    self.client_session.send(part_file)
                file_tranfer.close()


if __name__ == "__main__":
    Client().start()