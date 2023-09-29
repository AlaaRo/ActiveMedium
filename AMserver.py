#!/usr/bin/python3

# Central server handle clients


import socket,threading,logging

logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s',filename='serverlogs.txt')

s = socket.socket()
s.bind(('',4567)) #modify ip
s.listen(0)

end = b'\x02'
nickname_socks = dict()
bufsize = 2048

def reciever(sock,bufsize):
    total_recd = 0
    chunks = []
    while True:
        bytes_length = sock.recv(5)
        if bytes_length[-1] == 2:
            break
    length = int.from_bytes(bytes_length[:4],'big')
    while total_recd < length:
        chunk = sock.recv(bufsize)
        chunks.append(chunk)
        total_recd += len(chunk)
    full_msg = b''.join(chunks)
    return full_msg

def sender(sock,full_msg):
    total_sent = 0
    total_len = len(full_msg)
    length = total_len.to_bytes(4,'big')
    sock.sendall(length+end)
    while total_sent < total_len:
        sent = sock.send(full_msg)
        total_sent += sent
    return total_sent

def handler(clientsock,addr):
    """
    Handle operations on connections.
    """
    try:
        name = clientsock.recv(32).decode()
        nickname = name
        counter = 1
        while nickname in nickname_socks.keys():
            nickname = name + str(counter)
            counter += 1
        clientsock.sendall(nickname.encode())
        nickname_socks[nickname] = clientsock
        logging.info(f"{addr[0]}:{addr[1]} set nickname to {nickname}")
    
        while True:
            full_msg = reciever(clientsock,bufsize)
            if full_msg.startswith(b">>"):
                hosts = '>'.join(nickname_socks.keys())
                sender(clientsock,b">>"+hosts.encode())
                continue
            if full_msg.startswith(b'>'):
                msg_parts = full_msg.split(b'>',4)
                dest = msg_parts[1].decode()
            else:
                msg_parts = full_msg.split(b'>',2)
                dest = msg_parts[0].decode()
            sender(nickname_socks[dest],full_msg)
    
    except ConnectionResetError:
        to_remove = []
        for n,c in nickname_socks.items():
            if c == clientsock:
                to_remove.append(n)
        for n in to_remove:
            nickname_socks.pop(n)
        clientsock.close()
        logging.info(f"{addr[0]}:{addr[1]} Disconnected.")
    
while True:
    clientsock,addr = s.accept()
    threading.Thread(target=handler,args=(clientsock,addr),daemon=True).start()
    logging.info(f"{addr[0]}:{addr[1]} Connected.")
    
