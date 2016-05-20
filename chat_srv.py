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
list_users()      -- lists all users that are in the same channel as the user isssuing the query

Args:
sock              -- socket of the user issuing the query
curr_channel      -- channel of the user issuing the query

returns           -- 0 on success, -1 on failure
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
list_channels()   -- list all channels available

Args:
sock              -- socket of the user issuing the query
curr_channel      -- channel of the user issuing the query

returns           -- 0 on success, -1 on failure
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
        # Use * prefix to indicate the current channel
        if (channel == curr_channel):
            chat_rooms_msg += "    *{0}\n".format(channel)
        else: 
            chat_rooms_msg += "    {0}\n".format(channel)
    singlecast(sock, chat_rooms_msg)
    return 0

"""
leave_channel     -- remove user from their current channel, will remove channel if it is empty

Args:
sock              -- socket of the user issuing the query
curr_channel      -- channel of the user issuing the query
client_id         -- the port number of the client

returns           -- 0 on success, -1 on failure
Functions: 
        This function removes the user from their current channel, it will
        remove the channel if it is empty. It should be paired with a join_channel()
        so that the user isn't lost in ether.
"""
def leave_channel(sock, curr_channel, client_id):
    global CHAT_ROOMS
    # Search through all channels for the one with the client's id
    for channel in CHAT_ROOMS.itervalues():
        if (client_id in channel):
            channel.remove(client_id)
            if (not channel and curr_channel != "Home"):
                CHAT_ROOMS.pop(curr_channel)
            return 0
    print("[ERROR] leave_channel() could not find channel to leave")
    return -1

"""
join_channel      --  Adds the current user to a channel

Args:
srv_sock          -- socket belonging to the chat server
sock              -- socket of the user issuing the query
channel           -- channel the user wishes to join
client_id         -- the port number of the client

returns           -- 0 on success, -1 on failure
"""
def join_channel(srv_sock, sock, channel, client_id):
    global CHAT_ROOMS
    # Check to make sure channel exists, throw error if not
    if channel not in CHAT_ROOMS:
        no_channel_msg = "\n[ERROR] channel {0} does not exist\n".format(channel)
        singlecast(sock, no_channel_msg)
        return -1
    else:
        CHAT_ROOMS[channel].append(client_id)
        users = CHAT_ROOMS[channel]
        num_users = len(users)
        num_users_msg = "\nThere are {0} user(s) in {1}\n".format(num_users, channel)
        singlecast(sock, num_users_msg)
        print("added: {0} to {1}".format(client_id, channel))
    return 0

"""
create_channel    --  Adds a new channel

Args:
sock              -- socket of the user issuing the query
new_channel       -- channel the user wishes to create
client_id         -- the port number of the client

returns           -- 0 on success, -1 on failure
"""
def create_channel(sock, new_channel, client_id):
    global CHAT_ROOMS
    # If channel already exists notify the client
    if (new_channel in CHAT_ROOMS):
        chat_exists_msg = "\nChannel {0} already exists\n".format(new_channel)
        singlecast(sock, chat_exists_msg)
        return 0
    CHAT_ROOMS[new_channel] = []
    print("{0} created new chat room: {1}".format(client_id, new_channel))
    return 0

"""
handle_chat_cmd   -- This function handles all admin tasks for the client

Args:
srv_sock          -- socket belonging to the chat server
data              -- The full text of the message sent
sock              -- socket of the user issuing the query
client_port       -- the port number of the client
curr_channel      -- channel the user is in

Functions:
        This function is called anytime the client enters a '/' to begin
        the message. It handles all administrative tasks involved with
        changing channels and listing info.

returns           -- 0 on success, -1 on failure
"""
def handle_chat_cmd(srv_sock, data, sock, client_port, curr_channel):
    global USAGE
    global CHAT_ROOMS
    # Check to make sure user entered a valid option, if not throw error
    if (data[1] != 'x' and data[1] != 'l' and data[1] != 'u' and data[1] != 'c' and data[1] != 'j'):
        err_msg = "\nyou entered /{0} which is not a valid option, please try again\n".format(data[1])
        singlecast(sock, err_msg)
        singlecast(sock, USAGE)
        print("user {0} entered invalid option".format(client_port))
        return 0
    # e(x)it
    if (data[1] == 'x'):
        leave_channel(sock, curr_channel, client_port)
        print("CHAT _ROOMTS = ", CHAT_ROOMS)
        join_channel(srv_sock, sock, "Home", client_port)
        print("user {0} exited chat room".format(client_port))
        return 0 
    # (l)ist
    elif (data[1] == 'l'):
        channels = list_channels(sock, curr_channel)
        print("user {0} listed chat rooms".format(client_port))
        return 0
    # list (u)sers
    elif (data[1] == 'u'):
        users_msg = list_users(sock, curr_channel)
        print("user {0} listed users in chat room".format(client_port))
        return 0 
    else:
        # Strip out newline to simplify things
        data.rstrip('\n')
        # If data is less than 3 or there are no spaces the user has entered
        # an invalid command so send proper response and return
        if(len(data) <= 3 or ' ' not in data):
            err_msg = "\nPlease enter a channel\n"
            singlecast(sock, err_msg)
            return 0 
        cmd_tokenized = data.split()
        channel = cmd_tokenized[1]
        # (c)reate channel
        if (data[1] == 'c'):
            create_channel(sock, channel, client_port)
        # (j)oin channel
        elif (data[1] == 'j'):
            leave_channel(sock, curr_channel, client_port)
            join_channel(srv_sock, sock, channel, client_port)
        else:
            return -1
    return 0 

"""
handle_new_client() -- This function will initialize a new client

Args:
srv_sock            -- socket belonging to the chat server

Functions:
        This function initializes the clients, it sets them into the
        'Home' chat room, sends out a usage message, and broadcasts
        to other users to inform them of the new user.

returns           -- 0 on success, -1 on failure
"""
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


"""
event_loop() -- The main event loop of the server

Args:
srv_sock            -- socket belonging to the chat server

Functions:
        This function runs through all of the created connections. 
        It checks to see if there are any new clients, checks for 
        messages between other clients, and handles any administrative
        tasks, as well as handling dropped connections properly.

returns           -- 0 on success, -1 on failure
"""
def event_loop(srv_sock):
    global CHAT_ROOMS
    ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0)
      
    for sock in ready_to_read:
        if sock == srv_sock: 
            # Check to see if we have any new clients
            client_port = handle_new_client(srv_sock)
        else:
            try:
                # Data is a message coming from a client
                data = sock.recv(DATA_BUFF)
                client_port = sock.getpeername()[1]
                curr_channel = "Home" 
                # Cycle through the chat rooms till we find the one our current user belongs to
                for key in CHAT_ROOMS:
                    users_in_channel = CHAT_ROOMS[key]
                    if (client_port in users_in_channel):
                        curr_channel = key
                        break
                if data:
                    # If the message begins with a '/' it is handled as an administrative command
                    if (data[0] == '/'):
                        handle_chat_cmd(srv_sock, data, sock, client_port, curr_channel)
                        print("chat rooms = {0}".format(CHAT_ROOMS))
                    # Otherwise we broadcast the message to the rest of the users in the chat room
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
                                leave_channel(sock, channel, client_port)
                                print("client {0} left channel {1}".format(client_port, channel))
                    broadcast_to_channel(srv_sock, sock, "Client ({0}) is offline\n".format(client_port), curr_channel) 
            # Other failures are assumed to be dropped connections and handled here
            except:
                for channel in CHAT_ROOMS:
                    users_in_channel = CHAT_ROOMS[key]
                    if (client_port in users_in_channel):
                        curr_channel = channel 
                        leave_channel(sock, channel, client_port)
                broadcast_to_channel(srv_sock, sock, "Client ({0}) is offline\n".format(client_port), curr_channel)
                continue

"""
broadcast_to_channel() -- Broadcasts message to all users in channel

Args:
srv_sock               -- socket belonging to the chat server
sock                   -- socket of the user issuing the query
message                -- message to be sent
channel                -- channel the user is in

Function:
        This function sends out a message to all clients that are
        in the same chat room as the author of the message.

returns           -- 0 on success, -1 on failure
"""
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

"""
singlecast()           -- Send direct message to single client

Args:
sock                   -- socket of the user issuing the query
message                -- message to be sent

returns           -- 0 on success, -1 on failure
"""
def singlecast(sock, message):
    try:
        sock.send(message)
    except:
        print("[ERROR] singlecast() failed to send message")
        sock.close()
        return -1
    return 0
"""
init_chat_server() -- This function initializes the chat server
"""
def init_chat_server():
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

    sys.exit(init_chat_server())         

