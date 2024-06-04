import socket
import importlib
import time
from collections import defaultdict
import streamlit as st

# page functions
def nextpage(): 
    st.session_state.page += 1
def prevpage():
    st.session_state.page -= 1
def turnpage():
    st.session_state.page = 1

### button functions
def button1(HOST, PORT, user_info):
    PORT = int(PORT)
    try: 
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((HOST,PORT))
    except:
        st.warning('connection refused. try again.')
        return
    sending_data = "\n\n".join([str(user_info[k]) for k in user_info.keys()])
    sending_data = "ready\n\n" + sending_data
    server_socket.send(sending_data.encode())
    st.session_state.server_socket = server_socket
    data = server_socket.recv(1024).decode('utf-8')
    print(data)
    if data.split('\n\n')[0] == 'accepted':
        name = data.split('\n\n')[-1]
        st.session_state.name = name
        st.session_state.page += 1
    else:
        st.warning('player name duplicated.')

class DefaultClient:
    def __init__(self, fc, placeholder):
        self.fc = fc
        self.placeholder = placeholder
        pass

    def button2(self, **kwargs):
        # do something?
        # st.session_state.server_socket.send(f'bid\n\n{cur_bid}'.encode())
        st.session_state.session_control = False
        st.session_state.page += 1
    
    def button3(self, **kwargs):
        st.session_state.server_socket.send(f'end_turn'.encode())
        st.session_state.session_control = False
        st.session_state.page += 1

    # Define your own main page to get your requirments
    def main_page(self, HOST, PORT):
        with self.placeholder.container():
            st.write("Welcome to new Game!")

            st.write("Type your information and connect to your server!")
            name = st.text_input('Nickname', 'Tester')
            st.button("Connect", key='button1', on_click=button1, kwargs={'HOST': HOST, 'PORT': PORT, 'name': name}, disabled=st.session_state.page!=0)

    def turn_page(self):

        self.placeholder.write("Please wait until server start turn.")
        if not st.session_state.session_control:
            while True:
                data = st.session_state.server_socket.recv(1024).decode('utf-8')
                print(data)
                if data == 'start':
                    st.session_state.session_control = True
                    break
                else:
                    print('error?')

        # turn start
        with self.placeholder.container():
            st.write(f"**Turn {st.session_state.turn} started.**")
            user_info = st.container(border=True)
            # get turn status (if need)
            user_info.write(f"Your status")
            st.session_state.server_socket.send('get_player'.encode())
            data = st.session_state.server_socket.recv(1024).decode('utf-8')
            data_list = data.split('\n\n')
            print("print status")

            st.button("Turn end", key='button2', on_click=self.button2, disabled=st.session_state.page != 1)

    def turn_waiting_page(self):
        self.placeholder.write("Waiting other players finish bet...")
        while True:
            data = st.session_state.server_socket.recv(1024).decode('utf-8')
            data_list = data.split('\n\n')
            break

            ### if you use win/lose in one turn
            
            # if data_list[0] == 'end_turn':
            #     if data_list[1] == 'win':
            #         st.session_state.iswin = True
            #     elif data_list[1] == 'lose':
            #         st.session_state.iswin = False
            #     break
            # else:
            #     print('error?')
        with self.placeholder.container():
            st.write(f"**Turn {st.session_state.turn} ended.**")
            
            ### if you use win/lose in one turn
            # if st.session_state.iswin:
            #     st.write(f"*You won this turn! get {st.session_state.nowsup} supply, get 2 life.*")
            # else:
            #     st.write(f"You lost this turn. lost 1 life.")

            st.button("End turn", key='button3', on_click=self.button3)

    def turn_end_page(self):
        self.placeholder.write("Waiting other players finish checking result...")
        while True:
            data = st.session_state.server_socket.recv(1024).decode('utf-8')
            data_list = data.split('\n\n')
            if data_list[0] == 'end_game':
                onclick = nextpage
                break
            elif data_list[0] == 'start_turn':
                st.session_state.turn += 1
                onclick = turnpage
                break
            else:
                print('error?')

        with self.placeholder.container():
            st.write("Goto next turn's night..")
            st.button("Next", key='button4', on_click=onclick)

    def game_end_page(self):
        st.write("Not implemented.")
        # print result / save result / query....
    
