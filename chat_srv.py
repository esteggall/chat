# chat_server.py
# Code template for chat from: http://www.bogotobogo.com/python/python_network_programming_tcp_server_client_chat_server_chat_client_select.php
 
import sys, socket, select

HOSTNAME = ''
SOCKET_LIST = []
DATA_BUFF = 8192
PORT = 9009
NUM_LISTENERS = 64
CHAT_ROOMS = {}
USAGE = """
Chat Options:
     /c channel_name - (c)reate channel "channel_name"
     /j channel_name - (j)oin channel "channel_name" 
     /l - (l)ist channels" 
     /u - list (u)sers in current channel" 
     /x - e(x)it channel, this option returns you Home\n
"""
 
"""
list_users() -- lists all users that are in the same channel as the user isssuing the query
[IN] sock -- socket of the user issuing the query
[IN] channel -- channel of the user issuing the query
returns      -- 0 on success, -1 on failure
"""
def list_users(sock, curr_channel):
    global CHAT_ROOMS
    try:
        users = CHAT_ROOMS.get(curr_channel)
    except:
        print("[ERROR] failed to get users in list_users()")
        return -1
    users_msg = "\nUsers in {0}:\n".format(curr_channel)
    for usr in users:
        users_msg += str(usr) + '\n'
    singlecast(sock, users_msg)
    return 0
    
"""
list_channels() -- list all channels available
[IN] sock -- socket of the user issuing the query
[IN] channel -- channel of the user issuing the query
returns      -- 0 on success, -1 on failure
"""
def list_channels(sock, curr_channel):
    global CHAT_ROOMS
    try:
        chat_rooms = CHAT_ROOMS.keys()
    except:
        print("[ERROR] failed to get users in list_users()")
        return -1
    chat_rooms_msg = "\nAvailable Channels:\n"
    for channel in chat_rooms:
        # Use the * to indicate the current channel
        if (channel == curr_channel):
            chat_rooms_msg += "    *{0}\n".format(channel)
        else: 
            chat_rooms_msg += "    {0}\n".format(channel)
    singlecast(sock, chat_rooms_msg)
    return 0

"""
"""
def leave_channel(curr_channel, client_id, sock):
    global CHAT_ROOMS
    print("leaving channel {0} chat rooms = {1}".format(curr_channel, CHAT_ROOMS))
    for a in CHAT_ROOMS.itervalues():
        if( client_id in a):
            a.remove(client_id)
            print("leaving channel {0} chat rooms = {1}".format(curr_channel, CHAT_ROOMS))
            return 0
    print("[ERROR] could not find channel to leave")
    return -1

def join_channel(channel, client_id, sock):
    global CHAT_ROOMS
    if channel not in CHAT_ROOMS:
        no_channel_msg = "\n[ERROR] That channel does not exist\n"
        singlecast(sock, no_channel_msg)
        return -1
    else:
        CHAT_ROOMS[channel].append(client_id)
        print("added: {0} to {1}".format(client_id, channel))
    return 0

def create_channel(new_channel, client_id, sock):
    global CHAT_ROOMS
    if (new_channel in CHAT_ROOMS):
        chat_exists_msg = "\nChannel {0} already exists\n".format(new_channel)
        singlecast(sock, chat_exists_msg)
        return 0
    CHAT_ROOMS[new_channel] = []
    print("{0} created new chat room: {1}".format(client_id, new_channel))
    return 0

def handle_chat_cmd(data, sock, client_port, curr_channel):
    global USAGE
    if (data[1] != 'x' and data[1] != 'l' and data[1] != 'u' and data[1] != 'c' and data[1] != 'j'):
        err_msg = "\nyou entered /{0} which is not a valid option, please try again\n".format(data[1])
        singlecast(sock, err_msg)
        singlecast(sock, USAGE)
        print("user {0} entered invalid option".format(client_port))
        return 0
    if (data[1] == 'x'):
        leave_channel(curr_channel, client_port, sock)
        join_channel("Home", client_port, sock)
        print("user {0} exited chat room".format(client_port))
        return 0 
    elif (data[1] == 'l'):
        channels = list_channels(sock, curr_channel)
        print("user {0} listed chat rooms".format(client_port))
        return 0
    elif (data[1] == 'u'):
        users_msg = list_users(sock, curr_channel)
        print("user {0} listed users in chat room".format(client_port))
        return 0 
    else:
        data.rstrip('\n')
        if(len(data) <= 3 or ' ' not in data):
            err_msg = "\nPlease enter a channel\n"
            singlecast(sock, err_msg)
            return 0 
        cmd_tokenized = data.split()
        channel = cmd_tokenized[1]
        if (data[1] == 'c'):
            create_channel(channel, client_port, sock)
        elif (data[1] == 'j'):
            leave_channel(curr_channel, client_port, sock)
            join_channel(channel, client_port, sock)
        else:
            return -1
    return 0 


def handle_new_client(srv_sock):
    global CHAT_ROOMS
    global USAGE
    sockfd, addr = srv_sock.accept()
    # Addr is a tuple: (host, port)
    client_port = addr[1]
    SOCKET_LIST.append(sockfd)
    print "Client (%s, %s) connected" % addr
    CHAT_ROOMS["Home"].append(client_port)
    message = USAGE
    singlecast(sockfd, message) 
    list_channels(sockfd, "Home")
    broadcast_to_channel(srv_sock, sockfd, "[%s:%s] entered our chatting room\n" % addr, "Home")
    return client_port


def event_loop(srv_sock):
    global CHAT_ROOMS
    ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0)
      
    for sock in ready_to_read:
        if sock == srv_sock: 
            client_port = handle_new_client(srv_sock)
        else:
            try:
                print("chat rooms = {0}".format(CHAT_ROOMS))
                data = sock.recv(DATA_BUFF)
                client_port = sock.getpeername()[1]
                curr_channel = "Home" 
                for key in CHAT_ROOMS:
                    users_in_channel = CHAT_ROOMS[key]
                    if (client_port in users_in_channel):
                        curr_channel = key
                        break
                if data:
                    if (data[0] == '/'):
                        handle_chat_cmd(data, sock, client_port, curr_channel)
                    else:
                        print("client {0} wrote {1}".format(client_port, data))
                        broadcast_to_channel(srv_sock, sock, "\r" + curr_channel + ':[' + str(sock.getpeername()) + '] ' + data, curr_channel)  
                # Failed to recieve data here, remove user and broadcast user's departure 
                else:
                    if sock in SOCKET_LIST:
                        SOCKET_LIST.remove(sock)
                        for channel in CHAT_ROOMS:
                            users_in_channel = CHAT_ROOMS[key]
                            if (client_port in users_in_channel):
                                curr_channel = channel 
                                leave_channel(channel, client_port, sock)
                                print("client {0} left channel {1}".format(client_port, channel))
                    broadcast_to_channel(srv_sock, sock, "Client ({0}) is offline\n".format(client_port), curr_channel) 
            except:
                broadcast_to_channel(srv_sock, sock, "Client ({0}) is offline\n".format(client_port), curr_channel)
                continue


def broadcast_to_channel(srv_sock, sock, message, channel):
    global CHAT_ROOMS
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
                print("[ERROR] broadcast() failed to send message")
                socket.close()
                if socket in SOCKET_LIST:
                    SOCKET_LIST.remove(socket)

def singlecast(sock, message):
    try:
        sock.send(message)
    except:
        print("[ERROR] singlecast() failed to send message")
        sock.close()
        return -1
    return 0

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

