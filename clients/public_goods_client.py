from .default_client import *
import streamlit as st

def initpage():
    st.session_state.page = 0
def endpage():
    st.session_state.page = 4
def msgpage():
    st.session_state.page = 5

def sending_mail(player_msgs, time):
    sending = ""
    for pname, msg in player_msgs.items():
        if msg != "":
            sending += f"{pname}@{msg}\n\n" 

    st.session_state.server_socket.send(f'{time}\n\n{sending}'.encode())
    st.session_state.client_log[st.session_state.turn] += f"{time} Send \n\n"
    st.session_state.client_log[st.session_state.turn] += sending
    st.session_state.session_control = False
    if time == 'night':
        st.session_state.page += 1
    elif time == 'day':
        turnpage()
 
class PublicGoodsClient(DefaultClient):
    def __init__(self, placeholder):
        super().__init__(placeholder)
        pass

    def button2(self, **kwargs):
        cur_bid = kwargs['cur_bid']
        print(cur_bid)
        st.session_state.server_socket.send(f'bid\n\n{cur_bid}'.encode())
        st.session_state.session_control = False
        st.session_state.page += 1

    def button4(self, func):
        st.session_state.session_control = False
        func()

    ### page implementations
    def main_page(self, HOST, PORT):
        with self.placeholder.container():
            st.write("Welcome to new Game!")

            st.write("Type your information and connect to your server!")
            HOST = st.text_input('IP address', '')
            username = st.text_input('Your name for checking attendence', '')
            st.write("You will get new nickname when game started.")
            # persona = st.text_area('Persona', '')
            user_info = {
                "username": username
            }
            st.button("Connect", key='button1', on_click=button1, kwargs={'HOST': HOST, 'PORT': PORT, 'user_info': user_info}, disabled=st.session_state.page!=0)

    def turn_page(self):
        self.placeholder.write("Please wait until server start turn.")
        
            
        if not st.session_state.session_control:
            while True:
                data = st.session_state.server_socket.recv(1024).decode('utf-8')
                print(data)
                if data == 'start':
                    st.session_state.session_control = True
                    st.session_state.button_disabled = False
                    st.session_state.server_socket.send('get_player'.encode())
                    data = st.session_state.server_socket.recv(1024).decode('utf-8')
                    print(data)
                    st.session_state.player_data = data.split('\n\n')
                    if st.session_state.turn > 1:
                        if len(st.session_state.player_data) > 5:
                            dindex = -1
                            for i, d in enumerate(st.session_state.player_data):
                                if "Replys" in d:
                                    dindex = i
                                    break
                            
                            st.session_state.client_log[st.session_state.turn] += "day Received \n\n"
                            if dindex != -1:
                                st.session_state.client_log[st.session_state.turn] += '\n\n'.join(st.session_state.player_data[dindex:])
                    break
                else:
                    print('error?')
            

        # start turn
        with self.placeholder.container():
            st.write(f"**Turn {st.session_state.turn} started.**")

            ninfo = st.container(border=True)
            ninfo.write(f"You are {st.session_state.name}.")

            user_info = st.container(border=True)
            user_info.write(f"Your status")
            data_list = st.session_state.player_data
            user_info.write(f"")
            user_info.write(f"NAME: {data_list[0]}")
            user_info.write(f"ENDOWMENT:{data_list[1]}")
            user_info.write(f"FARE:{data_list[2]}")
            user_info.write(f"ENDOWMENT TARGET:{data_list[3]}")
            user_info.write("")
            user_info.write(f"Other players info:")
            for t in data_list[4].split('   '):
                user_info.write(t)
            if st.session_state.turn > 1:
                with st.sidebar:
                    st.title(f"{st.session_state.name} message box")
                    tab_list = st.tabs([f"Turn {i}" for i in range(1, st.session_state.turn+1)])
                    for i in range(1, st.session_state.turn+1):
                        tab_list[i-1].write(st.session_state.client_log[i])
            bc = st.container(border=True)
            cur_bid = bc.number_input('Current turn\'s contribution', min_value=0, max_value=int(data_list[1]))
            st.button("Bet!", key='button2', on_click=self.button2, kwargs={'cur_bid': cur_bid}, disabled=st.session_state.page != 1)
    
    def turn_waiting_page(self):
        self.placeholder.write("Waiting other players finish bet...")
        if not st.session_state.session_control:
            while True:
                data = st.session_state.server_socket.recv(1024).decode('utf-8')
                data_list = data.split('\n\n')
                if data_list[0] == 'end_turn':
                    st.session_state.session_control = True
                    st.session_state.player_data = data
                    st.session_state.client_log[st.session_state.turn] += "Endowment \n\n"
                    st.session_state.client_log[st.session_state.turn] += data_list[3]
                    st.session_state.client_log[st.session_state.turn] += "\n\nContribution\n\n"
                    st.session_state.client_log[st.session_state.turn] += data_list[4]
                    break
                else:
                    print('error?')
        data_list = st.session_state.player_data.split('\n\n')
        
        with self.placeholder.container():
            ec = st.container(border=True)
            ec.write(f"**Turn {st.session_state.turn} ended.**")
            ec.write(data_list[2])
            ec.write("Your After Endowment")
            ec.write(data_list[1])
            ec.write("Overall Endowment")
            ec.write(data_list[3])
            ec.write("Opponents' contributions")
            ec.write(data_list[4])
            onclick = self.button3
            if data_list[5] != 'none':
                ec.write(data_list[5])
                if int(data_list[1].split(':')[1]) < 0:
                    ec.write("You eliminated.")
                    onclick = endpage

            st.button("End turn", key='button3', on_click=onclick)


    def turn_end_page(self):
        self.placeholder.write("Waiting other players finish checking result...")
        if not st.session_state.session_control:
            while True:
                data = st.session_state.server_socket.recv(1024).decode('utf-8')
                data_list = data.split('\n\n')
                if data_list[0] == 'end_game':
                    st.session_state.session_control = True
                    onclick = self.button4(nextpage)
                    break
                elif data_list[0] == 'start_turn':
                    st.session_state.turn += 1
                    st.session_state.session_control = True
                    onclick = self.button4(msgpage)
                    break
                else:
                    print('error?')
        with self.placeholder.container():
            st.write("Goto next turn night...")
            st.button("Next", key='button4', on_click=onclick)

    def night_msg_page(self):
        self.placeholder.write("Waiting server start night...")
        
        if not st.session_state.session_control:
            while True:
                data = st.session_state.server_socket.recv(1024).decode('utf-8')
                if data == 'start':
                    st.session_state.session_control = True
                    break
        if st.session_state.turn > 1:
            with st.sidebar:
                st.title(f"{st.session_state.name} message box")
                tab_list = st.tabs([f"Turn {i}" for i in range(1, st.session_state.turn+1)])
                for i in range(1, st.session_state.turn+1):
                    tab_list[i-1].write(st.session_state.client_log[i])
        
        with self.placeholder.container():
            nmsgc = st.container(border=True)
            nmsgc.write("**Night Secret Mailbox**")
            nmsgc.write("Write secret messages to players..!")
            st.session_state.server_socket.send('get_player_name'.encode())
            data = st.session_state.server_socket.recv(1024).decode('utf-8')
            pname_list = data.split(' ')
            player_msgs = {}
            for pname in pname_list:
                if pname == st.session_state.name:
                    continue
                player_msgs[pname] = nmsgc.text_area(f'Message to {pname}')
            
            st.button('Send', key='nightsend', on_click=sending_mail, kwargs={'time':'night', 'player_msgs': player_msgs})
        
    
    def day_msg_page(self):
        self.placeholder.write("Waiting server start day...")

        
        if not st.session_state.session_control:
            while True:
                data = st.session_state.server_socket.recv(1024).decode('utf-8')
                data_list = data.split('\n\n')
                if data_list[0] == 'start':
                    st.session_state.session_control = True
                    st.session_state.rnames = []
                    st.session_state.rdatas = data_list[1:]
                    st.session_state.client_log[st.session_state.turn] += "night Received \n\n"
                    st.session_state.client_log[st.session_state.turn] += '\n\n'.join(data_list[1:])
                    for d in st.session_state.rdatas:
                        if d == "":
                            continue
                        if d.split(':')[0] == 'Messages':
                            st.session_state.rnames.append(d.split(':')[1])
                        else:
                            st.session_state.rnames.append(d.split(':')[0])
                    break
        if st.session_state.turn > 1:
            with st.sidebar:
                st.title(f"{st.session_state.name} message box")
                tab_list = st.tabs([f"Turn {i}" for i in range(1, st.session_state.turn+1)])
                for i in range(1, st.session_state.turn+1):
                    tab_list[i-1].write(st.session_state.client_log[i])
        with self.placeholder.container():
            nrmsgc = st.container(border=True)
            if len(st.session_state.rdatas) > 0:
                nrmsgc.write("You received messages:")
                for d in st.session_state.rdatas:
                    print(d)
                    if d == "":
                        continue
                    if d.split(':')[0] == 'Messages':
                        nrmsgc.write(f"{d.split(':')[1]}: {d.split(':')[2]}")
                    else:
                        nrmsgc.write(f"{d.split(':')[0]}: {d.split(':')[1]}")
                dmsgc = st.container(border=True)
                dmsgc.write("**Day Secret Mailbox**")
                dmsgc.write("Write reply!")
                player_msgs = {}
                for rname in st.session_state.rnames:
                    if rname != "":
                        player_msgs[rname] = dmsgc.text_area(f'Reply to {rname}', key=f'tadms{rname}')
                smsg = 'Send'
            else:
                nrmsgc.write("You received no messages.")
                player_msgs = {}
                smsg = 'Next'
            
            st.button(smsg, key='daysend', on_click=sending_mail, kwargs={'time': 'day', 'player_msgs': player_msgs})

    def game_end_page(self):
        st.write("The game ends.")

        st.button("Restart game", key='button6', on_click=initpage)