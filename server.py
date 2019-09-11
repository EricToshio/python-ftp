from socket import *
import os
import csv
import threading
import subprocess

def session_output(username:str,output:str)-> str:
    """Auxilia na criacao do output"""
    return  output+"\n"+username+"$"

def remove_repeat(direc:str)->str:
    """Auxilia na remocao de diretorios do tipo  '..' e '.' """
    dic_direc = direc.split('/')
    while ".." in dic_direc:
        loc = dic_direc.index("..")
        dic_direc.pop(loc)
        dic_direc.pop(loc-1)
    while "." in dic_direc:
        dic_direc.remove(".")
    while "" in dic_direc:
        dic_direc.remove("")
    new_direc = "/"
    for i in dic_direc:
        new_direc = new_direc+i+"/"
    return new_direc

class Server:
    def __init__(self, serverPort = 2121):
        """Classe que representa o servidor"""

        self.serverSocket = socket(AF_INET,SOCK_STREAM)
        self.serverSocket.bind(('',serverPort))
        self.serverSocket.listen(1)
        self.dir = remove_repeat(self.get_dir())
        self.cred = self.get_cred()
        
        print("Servidor ativado com sucesso")
    
    def get_cred(self)->list:
        """Obtem as credencias a partir do arquivo"""
        file = input("Arquivo com credenciais:")
        while not os.path.isfile(file):
            file = input("arquivo inexistente\nEscreva o nome de outro arquivo:")
        csv_file = open(file, mode='r')
        dici = list(csv.DictReader(csv_file))
        csv_file.close()
        return dici

    
    def get_dir(self)->str:
        """Obtem o diretorio base do servidor ftp"""
        dir = input("Diretorio base do servidor ftp:")
        while not os.path.isdir(dir) and dir[0]=='/':
            dir = input("Diretorio inexistente\nEscreva o nome de outro diretorio:")
        if dir[-1]=="/":
            dir = dir + "/" 
        return dir

    def autentication(self,conn,addr):
        """Faz a autenticacao antes de permitir a conexao do cliente"""
        conn.send("login:".encode())
        logout = False
        while not logout:
            
            username = str(conn.recv(1024).decode())
            conn.send("password:".encode())
            password = str(conn.recv(1024).decode())
            for user_cred in self.cred:
                # verificar o login
                if user_cred["username"]==username and user_cred["password"]==password:
                    # login com sucesso
                    conn.send(("Login realizado com sucesso\n"+username+"$").encode())
                    print(addr, "logou-se como", username)
                    self.client_listen(conn, addr,username, self.dir)
                    logout = True
            # login falhou
            if not logout: 
                conn.send("credenciais erradas, tente novamente\nlogin:".encode())

    def client_listen(self, conn, addr,user, dir):
        """Processa os comandos de cada um dos clientes"""
        running = True
        dir_actual = dir
        while running:
            text = conn.recv(1024).decode()
            command = text.split(' ')
            first_command = command[0]
            if first_command == "close" or first_command == "quit":
                running = False
            else:
                # comando CD
                if first_command == "cd":
                    if len(command) != 2:
                        output = "ERRO: numero de argumentos errado"
                    else:
                        if command[1][0]=="/":
                            new_path = command[1]
                        else:
                            new_path = dir_actual+command[1]
                        if not os.path.isdir(new_path):
                            output = "ERRO: Diretorio inexistente"
                        else:
                            dir_actual = new_path
                            dir_actual = remove_repeat(dir_actual)
                            output=""
                # comando LS e comando PWD
                elif first_command == "ls" or first_command == "pwd":
                    out = subprocess.Popen(command,stdout = subprocess.PIPE,cwd=dir_actual)
                    output = out.stdout.read().decode()[:-1]
                # comando MKDIR
                elif first_command == "mkdir":
                    if len(command) != 2:
                        output = "ERRO: numero de argumentos errado"
                    elif os.path.isdir(dir_actual+command[1]):
                        output = "ERRO: Diretorio ja existe"
                    else:
                        subprocess.Popen(command,stdout = subprocess.PIPE,cwd=dir_actual)
                        output=""
                # comando RMDIR
                elif first_command == "rmdir":
                    if len(command) != 2:
                        output = "ERRO: numero de argumentos errado"
                    elif not os.path.isdir(dir_actual+command[1]):
                        output = "ERRO: Diretorio inexistente"
                    else:
                        subprocess.Popen(["rm","-rf",command[1]],stdout = subprocess.PIPE,cwd=dir_actual)
                        output = ""
                # comando GET
                elif first_command == "get":
                    if len(command) != 2:
                        conn.send("FAIL".encode())
                        output = "ERRO: numero de argumentos errado"
                        conn.recv(1024)
                    elif not os.path.isfile(dir_actual+command[1]):
                        conn.send("FAIL".encode())
                        output = "ERRO: arquivo inexistente"
                        conn.recv(1024)
                    else:
                        conn.send("OK".encode())
                        if conn.recv(1024).decode() == "SIZE":
                            file_tranfer = open(dir_actual+command[1],'rb')
                            size = os.path.getsize(dir_actual+command[1])
                            packets = int(size/1024)
                            if size%1024!=0:
                                packets += 1
                            conn.send(str(packets).encode())
                            conn.recv(1024)
                            for _ in range(packets):
                                part_file = file_tranfer.read(1024)
                                conn.send(part_file)
                            file_tranfer.close()
                            conn.recv(1024)
                            output = "arquivo transferido com sucesso"
                        else:
                            output = "ERRO: operacao cancelada pelo usuario"
                # comando PUT
                elif first_command == "put":
                    conn.send("SEARCH".encode())
                    finish = False
                    if conn.recv(1024).decode() == "NOT_FOUND":
                        output = "ERRO: arquivo nao encontrado"
                    else:
                        if os.path.isfile(dir_actual+command[1]):
                            conn.send("HAVE_EQUAL".encode())
                            if conn.recv(1024).decode() == "ABORT":
                                output = "ERRO: operacao cancelada pelo usuario"
                                finish = True
                        else:
                            conn.send("HAVE_NOT_EQUAL".encode())
                            conn.recv(1024)
                        if not finish:
                            conn.send("SIZE".encode())
                            packets = int(conn.recv(1024).decode())
                            conn.send("OK".encode())
                            file_transfer = open(dir_actual+command[1], 'wb')
                            for _ in range(packets):
                                data = conn.recv(1024)
                                file_transfer.write(data)
                            file_transfer.close()
                            output = "arquivo transferido com sucesso"
                # comando DELETE
                elif first_command == "delete":
                    if len(command) != 2:
                        output = "ERRO: numero de argumentos errado"
                    elif not os.path.isfile(dir_actual+command[1]):
                        output = "ERRO: arquivo inexistente"
                    else:
                        subprocess.Popen(["rm", command[1]],stdout = subprocess.PIPE,cwd=dir_actual)
                        output = ""
                # comando INVALIDO
                else:
                    output = "comando invalido"
                conn.send(session_output(user,output).encode())
        conn.close()
        print(addr, user, "finalizou a conexao")
    
    def start(self):
        """Recebe as conexoes e para cada uma delas cria uma thread nova"""
        while True:
            connectionSocket, addr = self.serverSocket.accept()
            print(addr, "conectou-se")
            threading.Thread(target=self.autentication, args=(connectionSocket,addr,)).start()



if __name__ == "__main__":
    Server().start()