# Client code
# chat_cli.py
# code templat for chat client from: http://www.bogotobogo.com/python/python_network_programming_tcp_server_client_chat_server_chat_client_select.php

import sys, socket, select, time

CHAT_ROOM = "Me"
DATA_BUFF = 8192
 
def chat_client():
    global CHAT_ROOM
    if(len(sys.argv) < 3) :
        print 'Usage : python chat_client.py hostname port'
        sys.exit()

    host = sys.argv[1]
    port = int(sys.argv[2])
     
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
     
    # connect to remote host
    try :
        s.connect((host, port))
    except :
        print 'Unable to connect'
        sys.exit()
     
    print 'Connected to remote host. You can start sending messages'
    sys.stdout.write('[' + CHAT_ROOM + '] '); sys.stdout.flush()
     
    while 1:
        socket_list = [sys.stdin, s]
         
        # Get the list sockets which are readable
        ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [])
         
        for sock in ready_to_read:             
            if sock == s:
                # incoming message from remote server, s
                data = sock.recv(DATA_BUFF)
                if not data :
                    print '\nDisconnected from chat server'
                    sys.exit()
                else :
                    #print data
                    sys.stdout.write(data)
                    sys.stdout.write('[' + CHAT_ROOM + '] '); sys.stdout.flush()     
            
            else :
                # user entered a message
                msg = sys.stdin.readline()
                s.send(msg)
                time.sleep(0.1)
                """
                    if(msg[1] == 'j'):
                        channel = msg.split()[1]
                        if (channel):
                            CHAT_ROOM = channel
                        else:
                            print("[ERROR] Need to specify chat room")
                    elif(msg[1] == 'x'):
                        CHAT_ROOM = "Home" 
                """
        
                sys.stdout.write('[' + CHAT_ROOM + '] '); sys.stdout.flush() 
                if (msg[0] == '/'):
                    continue
                print(msg)

if __name__ == "__main__":

    sys.exit(chat_client())
