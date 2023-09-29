#!/usr/bin/python3

# Client connect to central server

import socket,threading,time
from tkinter import *
from tkinter.filedialog import askopenfilename
import subprocess as sp
import os

if not os.path.exists('temp'):
    os.mkdir('temp')
if not os.path.exists('RecievedFiles'):
    os.mkdir('RecievedFiles')
Beethoven9 = "Beethoven's 9th.mp3"
Beethoven8 = "Beethoven's 8th.mp3"
Beethoven7 = "Beethoven's 7th.mp3"
Beethoven6 = "Beethoven's 6th.mp3"
Beethoven5 = "Beethoven's 5th.mp3"
Beethoven4 = "Beethoven's 4th.mp3"
Beethoven3 = "Beethoven's 3rd.mp3"
Beethoven2 = "Beethoven's 2nd.mp3"
Beethoven1 = "Beethoven's 1st.mp3"
BWV243 = "BWV243.mp3"
TWV917 = "TWV917.mp3"

end = b'\x02'
root = Tk()
root.withdraw()
bufsize = 2048
server = ('127.0.0.1',4567)
c = socket.socket()
c.connect(server)

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

def player(music):
    pass

def cleaner():
    for chatfile in os.listdir('temp'):
        print(f"Removing {chatfile}...")
        os.unlink(f"temp/{chatfile}")
    root.destroy()
    root.quit()

def file_writer(full_msg):
    msg_parts = full_msg.split(b'>',4) #>dest>sender>filename>file
    print(msg_parts[:4])                 
    sender = msg_parts[2].decode()
    filename = msg_parts[3].decode()
    filebytes = msg_parts[4]
    print(f"Filebytes Length:{len(filebytes)}")
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
    print(chats)
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
root.columnconfigure(0,weight=1)
root.columnconfigure(1,weight=1)
root.columnconfigure(2,weight=4)
root.rowconfigure(0,weight=1)
root.rowconfigure(1,weight=1)
name_label = Label(root,text=f"Your nickname:{nickname}",font=('Arial',13,'italic'))
name_label.grid(row=0,column=1,sticky='N',padx=10,pady=10)
listbox = Listbox(root,bd=2,font=('Arial',13),width=12)
listbox.bind('<<ListboxSelect>>',lambda event:message())
scrollbar = Scrollbar(root,orient='vertical',command=listbox.yview)
textarea = Text(root,bd=5,width=45,height=34,state='disabled',bg='black',fg='yellow')
listbox.config(yscrollcommand=scrollbar.set)
#scrollbar.grid(row=0,column=0,sticky='N')
textarea.grid(row=0,column=2,sticky='SE')
listbox.grid(row=0,column=0,sticky='NW')
refresh_button = Button(root,text='Refresh',width=14,command=lambda:send_alg(b">>Refresh"))
refresh_button.grid(row=0,column=0)
b9 = Button(root,text='B9',font=('Arial',10,'bold italic'),command=lambda:player(Beethoven9),bg='black',fg='white')
b8 = Button(root,text='B8',font=('Arial',10,'bold italic'),command=lambda:player(Beethoven8),bg='black',fg='white')
b7 = Button(root,text='B7',font=('Arial',10,'bold italic'),command=lambda:player(Beethoven7),bg='black',fg='white')
b6 = Button(root,text='B6',font=('Arial',10,'bold italic'),command=lambda:player(Beethoven6),bg='black',fg='white')
b5 = Button(root,text='B5',font=('Arial',10,'bold italic'),command=lambda:player(Beethoven5),bg='black',fg='white')
b4 = Button(root,text='B4',font=('Arial',10,'bold italic'),command=lambda:player(Beethoven4),bg='black',fg='white')
b3 = Button(root,text='B3',font=('Arial',10,'bold italic'),command=lambda:player(Beethoven3),bg='black',fg='white')
b2 = Button(root,text='B2',font=('Arial',10,'bold italic'),command=lambda:player(Beethoven2),bg='black',fg='white')
b1 = Button(root,text='B1',font=('Arial',10,'bold italic'),command=lambda:player(Beethoven1),bg='black',fg='white')
m1 = Button(root,text='TWV 9:17',font=('Arial',10,'bold italic'),command=lambda:player(TWV917),bg='black',fg='white')
m2 = Button(root,text='BWV 243',font=('Arial',10,'bold italic'),command=lambda:player(BWV243),bg='black',fg='white')
print(root.grid_size())
'''b9.pack(side=LEFT)
b8.pack(side=LEFT)
b7.pack(side=LEFT)
b6.pack(side=LEFT)
b5.pack(side=LEFT)
b4.pack(side=LEFT)
b3.pack(side=LEFT)
b2.pack(side=LEFT)
b1.pack(side=LEFT)
m1.pack(side=LEFT)
m2.pack(side=LEFT)'''
root.deiconify()
threading.Thread(target=processor,daemon=True).start()
root.mainloop()
