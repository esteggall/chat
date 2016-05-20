# chat_server.py
# Code template for chat from: http://www.bogotobogo.com/python/python_network_programming_tcp_server_client_chat_server_chat_client_select.php
 
import sys, socket, select

HOSTNAME = ''
SOCKET_LIST = []
DATA_BUFF = 8192
PORT = 9009
NUM_LISTENERS = 64
CHAT_ROOMS = {}
CLIENT_TO_CHAT = []

def list_users(channel):
    users = CHAT_ROOMS.get(channel)
    print("users in chat room {0} are {1}".format(channel, users))
    users_msg = "\nUsers in {0}:\n".format(channel)
    for usr in users:
        print("user ", usr)
        users_msg += str(usr) + '\n'
    print("user message == \n {0}".format(users_msg))
    return users_msg
    
def list_channels(curr_channel):
    chat_rooms = CHAT_ROOMS.keys()
    print("Available Channels:")
    chat_rooms_msg = "\nAvailable Channels:\n"
    for channel in chat_rooms:
        if (channel == curr_channel):
            print("    *{0}".format(channel))
            chat_rooms_msg += "    *{0}\n".format(channel)
        else: 
            print("    {0}".format(channel))
            chat_rooms_msg += "    {0}\n".format(channel)
    return chat_rooms_msg

def leave_channel(channel, client_id, sock):
    for i, (channel,cli_id) in enumerate(CLIENT_TO_CHAT):
        if (cli_id == client_id):
            print("removing: {0},{1}".format(channel, cli_id))
            old_channel = channel
            del CLIENT_TO_CHAT[i]

    for a in CHAT_ROOMS.itervalues():
        print("a = ", a)
        if( client_id in a):
            a.remove(client_id)
            return 0
    print("[ERROR] could not find channel to leave")
    return -1

def join_channel(channel, client_id, sock):
    if channel not in CHAT_ROOMS:
        print("[ERROR] That channel does not exist")
        no_channel_msg = "\n[ERROR] That channel does not exist\n"
        singlecast(sock, no_channel_msg)
        return -1
    else:
        print("here")
        leave_channel(channel, client_id, sock)
        CLIENT_TO_CHAT.append((channel, client_id))
        CHAT_ROOMS[channel].append(client_id)
        print("added: {0} to {1}".format(client_id, channel))
    return 0

def create_channel(new_channel, client_id, sock):
    if (new_channel in CHAT_ROOMS):
        print("Channel {0} already exists".format(new_channel))
        chat_exists_msg = "\nChannel {0} already exists\n".format(new_channel)
        singlecast(sock, chat_exists_msg)
        return 0
    CHAT_ROOMS[new_channel] = []
    print("created new chat room: {0}".format(new_channel))
    return 0

#def handle_chat_cmd(data):


def handle_new_client(srv_sock):
    global CHAT_ROOMS
    global CLIENT_TO_CHAT
    sockfd, addr = srv_sock.accept()
    # Addr is a tuple: (host, port)
    client_port = addr[1]
    SOCKET_LIST.append(sockfd)
    print "Client (%s, %s) connected" % addr
    CHAT_ROOMS["Home"].append(client_port)
    CLIENT_TO_CHAT.append(("Home", client_port))
    message = """
Chat Options:
     /c channel_name - (c)reate channel "channel_name"
     /j channel_name - (j)oin channel "channel_name" 
     /l - (l)ist channels" 
     /u - list (u)sers in current channel" 
     /x - e(x)it channel, this option returns you Home\n"""
    singlecast(sockfd, message) 
    list_channels("Home")
    broadcast_to_channel(srv_sock, sockfd, "[%s:%s] entered our chatting room\n" % addr, "Home")
    return client_port


def event_loop(srv_sock):
    ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0)
      
    for sock in ready_to_read:
        if sock == srv_sock: 
            client_port = handle_new_client(srv_sock)
         
        else:
            try:
                data = sock.recv(DATA_BUFF)
                client_port = sock.getpeername()[1]
                curr_channel = "Home" 
                
                for channel,cli in CLIENT_TO_CHAT:
                    if cli == client_port:
                        curr_channel = channel
                        break
                if data:
                    if (data[0] == '/'):
                        if (data[1] == 'x'):
                            print("exiting chat room")
                            leave_channel(channel, client_port, sock)
                            join_channel("Home", client_port, sock)
                            continue;
                        elif (data[1] == 'l'):
                            print("listing chat rooms")
                            channels = list_channels(curr_channel)
                            singlecast(sock, channels)
                            continue;
                        elif (data[1] == 'u'):
                            print("listing users in chat room")
                            users_msg = list_users(curr_channel)
                            print(users_msg)
                            singlecast(sock, users_msg)
                            continue;
                        if (data[1] == 'c'):
                            channel = data.split()[1]
                            if not channel:
                                print("Please enter a channel")
                                continue
                            print("creating channel")
                            create_channel(channel, client_port, sock)
                            continue;
                        elif (data[1] == 'j'):
                            channel = data.split()[1]
                            if not channel:
                                print("Please enter a channel")
                                continue
                            print("joining chat room {0}".format(channel)) 
                            join_channel(channel, client_port, sock)
                            continue;
                        else:
                            print("you entered /{0} which is not a valid option, please try again".format(data[1]))
                            continue;
                    print("client {0} wrote {1}".format(client_port, data))
                    broadcast_to_channel(srv_sock, sock, "\r" + curr_channel + ':[' + str(sock.getpeername()) + '] ' + data, curr_channel)  
                else:
                    if sock in SOCKET_LIST:
                        SOCKET_LIST.remove(sock)
                        for (channel,cli_id) in CLIENT_TO_CHAT:
                            if (cli_id == client_port):
                                leave_channel(channel, client_port, sock)
                                print("client {0} left channel {1}".format(client_port, channel))
                    broadcast_to_channel(srv_sock, sock, "Client ({0}) is offline\n".format(client_port), curr_channel) 
            except:
                broadcast_to_channel(srv_sock, sock, "Client ({0}) is offline\n".format(client_port), curr_channel)
                continue


def broadcast_to_channel(srv_sock, sock, message, channel):
    peers = CHAT_ROOMS.get(channel, None)
    print("peers in chat {0}".format(peers))
    for socket in SOCKET_LIST:
        if socket != srv_sock and socket != sock :
            client_port = socket.getpeername()[1]
            if (client_port not in peers):
                continue
            try :
                socket.send(message)
            except :
                socket.close()
                if socket in SOCKET_LIST:
                    SOCKET_LIST.remove(socket)

def singlecast(sock, message):
    try:
        sock.send(message)
    except:
        sock.close()

def chat_server():
    global SOCKET_LIST
    global CHAT_ROOMS
    srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv_sock.bind((HOSTNAME, PORT))
    srv_sock.listen(NUM_LISTENERS)
    SOCKET_LIST.append(srv_sock)
    CHAT_ROOMS["Home"] = []
    print("Started chat server on port {0}".format(str(PORT)))
    while 1:
        event_loop(srv_sock)

    srv_sock.close()
 
if __name__ == "__main__":
    global PORT
    if (sys.argv[1]):
        PORT = int(sys.argv[1])

    sys.exit(chat_server())         

