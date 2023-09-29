#!/usr/bin/python3

# Client connect to central server
# run: py AM1.py [SERVER_IP]
import socket,threading,sys
from time import sleep
from tkinter import *
from tkinter.filedialog import askopenfilename
import os

if not os.path.exists('temp'):
    os.mkdir('temp')
if not os.path.exists('RecievedFiles'):
    os.mkdir('RecievedFiles')
    
end = b'\x02'
root = Tk()
root.withdraw()
bufsize = 2048
try:
    server=(sys.argv[1],4567)
except IndexError:
    server=('127.0.0.1',4567)
c = socket.socket()
try:
    c.connect(server)
except ConnectionRefusedError:
    print("Connection Refused, check IP address, port number and the server.")
    sleep(15)
    sys.exit()
    
def namer(event):
    global nickname
    name = en.get()
    if name == '':
        return
    c.sendall('?'.join(name.split('>')).encode()) # '>' forbidden
    nickname = c.recv(bufsize).decode()
    nw.destroy()
    nw.quit()

nw = Tk()
nw.title("NICKNAME(1-32)")
en = Entry(nw,font=('Arial',16,'italic'),fg='black',bg='green',bd=5,relief=SUNKEN,width=50)
en.bind('<Return>',namer)
en.pack(anchor='s',expand=True,fill='x')
nw.mainloop()

def dir_maker(path):
    if not os.path.exists(path):
        os.mkdir(path)

def send_alg(full_msg):
    total_sent = 0
    total_len = len(full_msg)
    length = total_len.to_bytes(4,'big') #return 'bytes' object
    c.sendall(length+end)
    while total_sent < total_len:
        sent = c.send(full_msg) #already encoded
        total_sent += sent
    return total_sent

def reciever(bufsize):
    total_recd = 0
    chunks = []
    while True:
        bytes_length = c.recv(5)
        if bytes_length[-1] == 2:
            break
    length = int.from_bytes(bytes_length[:4],'big')
    while total_recd < length:
        chunk = c.recv(bufsize)
        chunks.append(chunk)
        total_recd += len(chunk)
    full_msg = b''.join(chunks)
    return full_msg

def cleaner():
    for chatfile in os.listdir('temp'):
        os.unlink(f"temp/{chatfile}")
    root.destroy()
    root.quit()

def file_writer(full_msg):
    msg_parts = full_msg.split(b'>',4) #>dest>sender>filename>file  
    sender = msg_parts[2].decode()
    filename = msg_parts[3].decode()
    filebytes = msg_parts[4]
    dir_maker(f"RecievedFiles/{sender}")
    with open(f"RecievedFiles/{sender}/{filename}",'wb') as f:
        f.write(filebytes)
    if sender in chats:
        chats[sender].configure(state='normal')
        chats[sender].insert(END,f"\nRecieved \"{filename}\" from {sender}.")
        chats[sender].configure(state='disabled')
    else:
        textarea.configure(state='normal')
        textarea.insert(END,f"\nRecieved \"{filename}\" from {sender}.")
        textarea.configure(state='disabled')
    with open(f"temp/chat_{sender}.txt",'a') as f:
        f.write(f"\nRecieved \"{filename}\" from {sender}.")

def msg_writer(full_msg):
    msg_parts = full_msg.split(b'>',2)
    sender = msg_parts[1].decode()
    msg = msg_parts[2].decode()
    form = f"\n{sender}>{msg}"
    if sender in chats:
        chats[sender].configure(state='normal')
        chats[sender].insert(END,form)
        chats[sender].configure(state='disabled')
    else:
        textarea.configure(state='normal')
        textarea.insert(END,form)
        textarea.configure(state='disabled')
    with open(f"temp/chat_{sender}.txt","a") as f:
        f.write(form)              

def closer(window,dest):
    chats.pop(dest)
    window.destroy()

def processor():
    while True:
        full_msg = reciever(bufsize)
        if full_msg.startswith(b">>"): # >>host1>host2>...>hostN
            listbox.delete(0,END)
            for host in full_msg.decode().split('>')[2:]:
                if host != nickname:
                    listbox.insert(END,host)
            continue
        if full_msg.startswith(b">"):
            file_writer(full_msg)
            continue
        msg_writer(full_msg)

def send_msg(destination,msg_entry,text_area):
    msg = msg_entry.get()
    if msg == '':
        return
    full_msg = f"{destination}>{nickname}>{msg}".encode()
    send_alg(full_msg)
    with open(f"temp/chat_{destination}.txt",'a') as f:
        f.write(f"\n{nickname}>{msg}")
    msg_entry.delete(0,END)
    text_area.configure(state='normal')
    text_area.insert(END,f"\n{nickname}>{msg}")
    text_area.configure(state='disabled')

def message():
    try:
        dest = listbox.get(listbox.curselection())
        if dest in chats:
            return
    except TclError:
        return
    window = Toplevel(root,bd=5,relief=SUNKEN)
    window.geometry('800x600')
    window.title(f"with {dest}")
    window.protocol("WM_DELETE_WINDOW",lambda:closer(window,dest))
    e = Entry(window,bd=5,relief=RAISED,width=50,font=('Arial',16),bg='green',fg='black')
    b = Button(window,bd=5,text='Isaiah6:8',activebackground='blue',font=('Arial',10,'bold'),bg='green',command=lambda:send_msg(dest,e,t))
    t = Text(window,bd=5,relief=SUNKEN,height=35,width=75,bg='green',fg='black')
    filebutton = Button(window,bd=5,relief=RAISED,bg='green',activebackground='blue',text='FileSend',font=('Arial',10,'bold'),command=lambda:send_file(dest))
    e.bind("<Return>",lambda event:send_msg(dest,e,t))
    chats[dest] = t
    dir_maker(f"RecievedFiles/{dest}")
    if os.path.exists(f"temp/chat_{dest}.txt"):
        with open(f"temp/chat_{dest}.txt","r") as f:
            chat_contents = f.read()
            t.insert(END,chat_contents)
            t.configure(state='disabled')
    else:
        t.configure(state='disabled') #just to make sure textarea is not enabled when not needed       
    t.place(x=0,y=0)
    e.place(x=0,y=563)
    b.place(x=613,y=560)
    filebutton.place(x=613,y=527)

def send_file(destination):
    filepath = askopenfilename() #list of absolute paths
    if filepath == []:
        return
    basename = os.path.basename(filepath)
    with open(filepath,"rb") as f:
        filebytes = f.read()
    prefix = f">{destination}>{nickname}>{basename}>".encode() 
    send_alg(prefix+filebytes)
    chats[destination].configure(state='normal')
    chats[destination].insert(END,f"\nSent \"{basename}\".")    
    chats[destination].configure(state='disabled')
    with open(f"temp/chat_{destination}.txt",'a') as f:
        f.write(f"\nSent \"{basename}\".")    

dir_maker('temp')
dir_maker('RecievedFiles')
chats = dict() #(key:value) : (sender:textarea)
root.title('ACTIVE MEDIUM: Main Window')
root.geometry('800x600')
root.protocol("WM_DELETE_WINDOW",cleaner)
root.configure(relief=SUNKEN,bd=5)
name_label = Label(root,text=f"Your nickname:{nickname}",font=('Arial',13,'italic'))
name_label.place(x=130,y=0)
listbox = Listbox(root,bd=2,font=('Arial',13),width=12)
listbox.bind('<<ListboxSelect>>',lambda event:message())
scrollbar = Scrollbar(root,orient='vertical',command=listbox.yview)
textarea = Text(root,bd=5,width=45,height=34,state='disabled',bg='black',fg='yellow')
listbox.config(yscrollcommand=scrollbar.set)
scrollbar.place(x=110,y=0)
textarea.place(x=420,y=0)
listbox.place(x=0,y=0)
refresh_button = Button(root,text='Refresh',width=14,command=lambda:send_alg(b">>Refresh"))
refresh_button.place(x=5,y=200)
root.deiconify()
threading.Thread(target=processor,daemon=True).start()
root.mainloop()
