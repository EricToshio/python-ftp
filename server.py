from socket import *
import os
import csv
import threading
import subprocess

def session_output(username:str,output:str)-> str:
    return  output+"\n"+username+"$"

def remove_repeat(direc:str)->str:
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
        self.serverSocket = socket(AF_INET,SOCK_STREAM)
        self.serverSocket.bind(('',serverPort))
        self.serverSocket.listen(1)
        #self.dir = remove_repeat(self.get_dir())
        self.cred = self.get_cred()
        self.dir = "/home/toshio/Desktop/teste/"
        
        print("Servidor ativado com sucesso")
    
    def get_cred(self)->dict:
        #file = input("Arquivo com credenciais:")
        ###################REMOVER###############
        file = "/home/toshio/Documents/projects/python-ftp/credential.csv"
        #########################################
        while not os.path.isfile(file):
            file = input("arquivo inexistente\nEscreva o nome deoutro arquivo:")
        csv_file = open(file, mode='r')
        return csv.DictReader(csv_file)

    
    def get_dir(self)->str:
        dir = input("Diretorio base do servidor ftp:")
        while not os.path.isdir(dir):
            dir = input("Diretorio inexistente\nEscreva o nome de outro diretorio:")
        if dir[-1]=="/":
            dir = dir + "/" 
        return dir

    def autentication(self,conn,addr):
        conn.send("login:".encode())
        while True:
            logout=False
            username = conn.recv(1024).decode()
            conn.send("password:".encode())
            password = conn.recv(1024).decode()
            ###########REMOVER
            username = "kali"
            password = "toor"
            ###########
            for user_cred in self.cred:
                if user_cred["username"]==username and user_cred["password"]==password: 
                    conn.send(("Login realizado com sucesso\n"+username+"$").encode())
                    print(addr, "logou-se como", username)
                    self.client_listen(conn, addr,username, self.dir)
                    logout = True
                    break
            if logout: break
            conn.send("credenciais erradas, tente novamente\nlogin:".encode())

    def client_listen(self, conn, addr,user, dir):
        running = True
        dir_actual = dir
        while running:
            text = conn.recv(1024).decode()
            command = text.split(' ')
            first_command = command[0]
            if first_command == "close" or first_command == "quit":
                running = False
            else:
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
                            #print("novo diretorio:",dir_actual)
                            output=""
                elif first_command == "ls" or first_command == "pwd":
                    out = subprocess.Popen(command,stdout = subprocess.PIPE,cwd=dir_actual)
                    output = out.stdout.read().decode()[:-1]
                elif first_command == "mkdir":
                    if len(command) != 2:
                        output = "ERRO: numero de argumentos errado"
                    elif os.path.isdir(dir_actual+command[1]):
                        output = "ERRO: Diretorio ja existe"
                    else:
                        subprocess.Popen(command,stdout = subprocess.PIPE,cwd=dir_actual)
                        output=""
                elif first_command == "rmdir":
                    if len(command) != 2:
                        output = "ERRO: numero de argumentos errado"
                    elif not os.path.isdir(dir_actual+command[1]):
                        output = "ERRO: Diretorio inexistente"
                    else:
                        subprocess.Popen(command,stdout = subprocess.PIPE,cwd=dir_actual)
                        output = ""
                elif first_command == "get":
                    if len(command) != 2:
                        conn.send("FAIL".encode())
                        output = "ERRO: numero de argumentos errado"
                    elif not os.path.isfile(dir_actual+command[1]):
                        conn.send("FAIL".encode())
                        output = "ERRO: arquivo inexistente"
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
                elif first_command == "put":
                    if conn.recv(1024).decode() == "NOT_FOUND":
                        output = "ERRO: arquivo nao encontrado"
                    else:
                        if os.path.isfile(command[1]):
                            conn.send("HAVE_EQUAL".encode())
                        else:
                            conn.send("NOT_HAVE_EQUAL".encode())
                        if conn.recv(1024).decode() == "ABORT":
                            output = "ERRO: operacao cancelada pelo usuario"
                        else:
                            

                elif first_command == "remove":
                    if len(command) != 2:
                        output = "ERRO: numero de argumentos errado"
                    elif not os.path.isfile(dir_actual+command[1]):
                        output = "ERRO: arquivo inexistente"
                    else:
                        subprocess.Popen(["rm", command[1]],stdout = subprocess.PIPE,cwd=dir_actual)
                        output = ""
                else:
                    output = "comando invalido"
                conn.send(session_output(user,output).encode())
        conn.close()
        print(addr, user, "finalizou a conexao")
    

        


    def start(self):
        while True:
            connectionSocket, addr = self.serverSocket.accept()
            print(addr, "conectou-se")
            threading.Thread(target=self.autentication, args=(connectionSocket,addr,)).start()



if __name__ == "__main__":
    Server().start()