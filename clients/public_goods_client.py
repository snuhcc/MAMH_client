from .default_client import *
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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
    st.session_state.client_log[st.session_state.turn] += sending.replace('@', ': ')
    for sends in sending.replace('@', ': ').split('\n\n'):
        if ':' in sends:
            name, msg = sends.split(':')
            st.session_state.message_logdict[name.strip()] += f"{st.session_state.turn}:(send){msg}\n\n"
    st.session_state.client_log[st.session_state.turn] += "\n\n --- \n\n"
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
            st.markdown("### 🎮 Welcome to the New Game!")

            st.write("Type your information and connect to your server!")
            HOST = st.text_input('🌐 IP Address', value='13.125.250.236')
            PORT = st.text_input('🌐 PORT', value=20912)
            username = st.text_input('📛 Your Name', '')
            st.write("You will receive a new nickname when the game starts.")
            # persona = st.text_area('Persona', '')
            user_info = {
                "username": username
            }
            st.button("🔗 Connect", key='button1', on_click=button1, kwargs={'HOST': HOST, 'PORT': PORT, 'user_info': user_info}, disabled=st.session_state.page!=0)

    def turn_page(self):
        with self.placeholder:
            with st.spinner("⌛ Please wait until the server starts the turn."):
                if not st.session_state.session_control:
                    data = ""
                    data_list = []
                    while 'start' not in data_list:
                        data = st.session_state.server_socket.recv(1024).decode('utf-8')
                        data_list = data.split('\n\n')
                    st.session_state.session_control = True
                    st.session_state.button_disabled = False
                    st.session_state.server_socket.send('get_player'.encode())
                    while st.session_state.name not in data:
                        data = st.session_state.server_socket.recv(1024).decode('utf-8')
                    data = st.session_state.name + st.session_state.name.join(data.split(st.session_state.name)[1:])
                    st.session_state.player_data = data.split('\n\n')

                    if st.session_state.turn > 1:
                        st.session_state.server_socket.send('get_msg'.encode())
                        reply_data = st.session_state.server_socket.recv(1024).decode('utf-8')
                        while 'msg' not in reply_data:
                            reply_data = st.session_state.server_socket.recv(1024).decode('utf-8')
                        st.session_state.client_log[st.session_state.turn] += "\n\nday Received \n\n"
                        all_replys = 'Replys'.join(reply_data.split('Replys:')[1:])
                        st.session_state.client_log[st.session_state.turn] += all_replys
                        for reply in all_replys.split('\n\n'):
                            if ':' in reply:
                                name, msg = reply.split(':')
                                st.session_state.message_logdict[name.strip()] += f"{st.session_state.turn-1}:(received){msg}\n\n"
        # start turn
        with self.placeholder.container():
            data_list = st.session_state.player_data
            st.markdown(f"### Turn {st.session_state.turn} / 8 started.")
            st.markdown(f"👤 **You are {st.session_state.name}.**")
            on = st.toggle(f"Click to see Round Rule.")
            if on:
                st.markdown(f"  -   You need to pay {data_list[2]} fare.")
                st.markdown(f"  -   Project will be success if all contribution is over {data_list[3]}.")
                st.markdown(f"  -   If project success, you will receive an amount distributed according to the number of people, twice the total.")
                st.markdown(f"  -   If project fail, you get nothing.")
                st.markdown(f"  -   For example, if all people bid at least {int(data_list[2]) // 2}, you can deserve all {data_list[2]} fare.")
                st.markdown("   -   Contribute smart to survive 8 rounds!")

            st.markdown(f"#### **Your status**")
            col1, col2 = st.columns(2)
            col1.image(f'person_images/{st.session_state.name}.png')
            col2.write(f"**Name**       : {data_list[0]}")
            col2.write(f"**Endowment**  : {data_list[1]}")

            
            other_players_info = data_list[4].split('   ')[:-1]
            cols = st.columns(len(other_players_info)) # TODO: make dynamic
            for i, col in enumerate(cols):
                c_name = other_players_info[i].split(':')[0][1:]
                c_endowment = other_players_info[i].split('- ')[-1].split(' ')[0]
                col.write(f"{c_name}")
                col.image(f'person_images/{c_name}.png')
                col.write(f"**Endowment :** {c_endowment}")
            
            if st.session_state.turn > 1:
                with st.sidebar:
                    st.title(f"📥 {st.session_state.name}'s Message Box")
                    names = st.session_state.status_logdict.keys()
                    names.remove(st.session_state.name)
                    selected = st.radio('Select one to see chats.', names, horizontal=True)
                    if selected in names:
                        st.write(f"endowment: {st.session_state.status_logdict[selected]}")
                        for msgs in st.session_state.message_logdict[selected.strip()].split('\n\n'):
                            if "(received)" in msgs:
                                name, msg = msgs.split("(received)")
                                with st.chat_message('assistant', avatar=f'person_images/{selected.strip()}.png'):
                                    st.write(msg)
                            elif "(send)" in msgs:
                                name, msg = msgs.split("(send)")
                                with st.chat_message('user', avatar=f'person_images/{st.session_state.name}.png'):
                                    st.write(msg)


            st.markdown(f"### **Contribution for Turn {st.session_state.turn}**")
            cur_bid = st.number_input("💰 Contribution", min_value=0, max_value=int(data_list[1]))
            st.button("🛠️ Bet", key='button2', on_click=self.button2, kwargs={'cur_bid': cur_bid}, disabled=st.session_state.page != 1)
    
    def turn_waiting_page(self):
        with self.placeholder:
            with st.spinner("⌛ Waiting for other players to finish betting..."):
                if not st.session_state.session_control:
                    data = ""
                    while 'end_turn' not in data:
                        data = st.session_state.server_socket.recv(1024).decode('utf-8')
                    data_list = data.split('\n\n')
                    st.session_state.server_socket.send('received'.encode())
                    st.session_state.session_control = True
                    st.session_state.player_data = data
                    endo_splits = data_list[2].split('\n')
                    cont_splits = data_list[3].split('\n')
                    endo_str = '  '.join(endo_splits)
                    cont_str = '  '.join(cont_splits)
                    st.session_state.client_log[st.session_state.turn] = f"**Endowment**\n\n{endo_str}\n\n**Contribution**\n\n{cont_str}\n\n --- \n\n"+ st.session_state.client_log[st.session_state.turn]
                    for i in range(len(endo_splits)):
                        if ':' in endo_splits[i]:
                            name, endo = endo_splits[i].split(':') 
                            st.session_state.status_logdict[name] = endo

                data_list = st.session_state.player_data.split('\n\n')
                
                ed_list = data_list[2].split("\n")
                ed_str = ""
                cur_ed = 0
                for i, ed in enumerate(ed_list):
                    if st.session_state.name in ed:
                        ed_str = ed
                        cur_ed = int(ed.split(":")[1].strip())

        with self.placeholder.container():
            col1, col2, col3 = st.columns([1,2,1])
            col2.write(f"#### 🏦 {data_list[1]}")
            st.markdown(f"### Turn {st.session_state.turn} Ended")
            st.markdown("#### **Your After Endowment**")
            col1, col2 = st.columns(2)
            col1.image(f'person_images/{st.session_state.name}.png', width=250)
            col2.write(f"**Name**       : {ed_str.split(':')[0].strip()}")
            col2.write(f"**Endowment**  : {ed_str.split(':')[1].strip()}")
            st.markdown("#### **Overall Endowment**")
            cols = st.columns(6) # TODO: make dynamic
            other_players_info = data_list[2].split('\n')
            other_players_cont = data_list[3].split('\n')
            for i, col in enumerate(cols):
                c_name = other_players_info[i].split(':')[0].strip()
                c_endowment = other_players_info[i].split(':')[1].strip()
                c_contribution = other_players_cont[i].split(':')[1].strip()
                str_endowment = "\n" + c_endowment
                str_contribution = "\n" + c_contribution
                if c_name not in st.session_state.contribution_table.keys():
                    st.session_state.contribution_table[c_name] = [0, int(c_contribution)]
                else:
                    st.session_state.contribution_table[c_name].append(int(c_contribution))
                if c_name not in st.session_state.endowment_table.keys():
                    st.session_state.endowment_table[c_name] = [1200, int(c_endowment)] # TODO: dynamic init endo
                else:
                    st.session_state.endowment_table[c_name].append(int(c_endowment))
                col.write(f"{c_name}")
                col.image(f'person_images/{c_name}.png')
                col.markdown(f"**Contribution**  {str_contribution}")
                col.markdown(f"**Endowment**   {str_endowment}")
                
                
            onclick = self.button3
            if data_list[4] != 'none':
                st.write('\n\n'.join(data_list[4].split('\n')))

                if cur_ed < 0:
                    st.write("❌ You have been eliminated.")
                    onclick = endpage

            st.button("➡️ End Turn", key='button3', on_click=onclick)


    def turn_end_page(self):
        with self.placeholder:
            with st.spinner("⌛ Waiting for other players to finish checking results..."):
                if not st.session_state.session_control:
                    data = ""
                    while 'end_game' not in data and 'start_turn' not in data:
                        data = st.session_state.server_socket.recv(1024).decode('utf-8')
                    data_list = data.split('\n\n')
                    if data_list[0] == 'end_game':
                        st.session_state.server_socket.send('received'.encode())
                        st.session_state.session_control = True
                        onclick = self.button4(nextpage)
                    elif data_list[0] == 'start_turn':
                        st.session_state.server_socket.send('received'.encode())
                        st.session_state.turn += 1
                        st.session_state.session_control = True
                        onclick = self.button4(msgpage)
        with self.placeholder.container():
            st.write("🌒 Goto Next Turn Night...")
            st.button("➡️ Next", key='button4', on_click=onclick)

    def night_msg_page(self):
        with self.placeholder:
            with st.spinner("🌒 Waiting for the server to start night..."):
                if not st.session_state.session_control:
                    data = ""
                    while 'start' not in data:
                        data = st.session_state.server_socket.recv(1024).decode('utf-8')
                    st.session_state.server_socket.send('received'.encode())
                    st.session_state.session_control = True
                    st.session_state.server_socket.send('get_player_name'.encode())
                    while 'player_name' not in data:
                        data = st.session_state.server_socket.recv(1024).decode('utf-8')
                    pname_list = data.split('player_name')[-1].split(' ')
                    pname_list = [item.replace("start", "") for item in pname_list if item != 'start']
                    st.session_state.pname_list = pname_list
            

        
        with self.placeholder.container():
            with st.sidebar:
                st.title(f"📥 {st.session_state.name}'s Message Box")
                names = st.session_state.status_logdict.keys()
                names.remove(st.session_state.name)
                selected = st.radio('Select one to see chats.', names, horizontal=True)
                if selected in names:
                    st.write(f"endowment: {st.session_state.status_logdict[selected]}")
                    for msgs in st.session_state.message_logdict[selected.strip().strip()].split('\n\n'):
                        if "(received)" in msgs:
                            name, msg = msgs.split("(received)")
                            with st.chat_message(name='assistant', avatar=f'person_images/{selected.strip()}.png'):
                                st.write(msg)
                        elif "(send)" in msgs:
                            name, msg = msgs.split("(send)")
                            with st.chat_message(name='user', avatar=f'person_images/{st.session_state.name}.png'):
                                st.write(msg)
            st.markdown("### 🌒 **Night Secret Mailbox**")
            st.write("Write secret messages to other players!")
            st.write("  -   You can write message as Korean, but please avoid using abbreviations or slang if possible.")
            st.write("  -   Your message will be translated, proofread and delivered in English to opponents.")
        
            contribution_df = pd.DataFrame(st.session_state.contribution_table)
            contribution_df.columns = [name[0] for name in contribution_df.columns]
            contribution_df['turn'] = list(range(0, st.session_state.turn))
            endowment_df = pd.DataFrame(st.session_state.endowment_table)
            endowment_df.columns = [name[0] for name in endowment_df.columns]
            endowment_df['turn'] = list(range(0, st.session_state.turn))
                
            col1, col2 = st.columns(2)
            col1.write("Contributions")
            col1.line_chart(contribution_df.set_index('turn'))
            col2.write("Endowments")
            col2.line_chart(endowment_df.set_index('turn'))


            player_msgs = {}
            for pname in st.session_state.pname_list:
                if pname == st.session_state.name or pname.strip() == "":
                    continue
                player_msgs[pname] = st.text_area(f"📧 Message to {pname}")
            
            st.button('📤 Send', key='nightsend', on_click=sending_mail, kwargs={'time':'night', 'player_msgs': player_msgs})
        
    
    def day_msg_page(self):
        with self.placeholder:
            with st.spinner("🌞 Waiting for the server to start day..."):
                if not st.session_state.session_control:
                    data = ""
                    while 'reply' not in data:
                        data = st.session_state.server_socket.recv(1024).decode('utf-8')
                    data_list = data.split('replys')[1].split('\n\n')
                    st.session_state.server_socket.send('received'.encode())
                    st.session_state.session_control = True
                    st.session_state.rnames = []
                    st.session_state.rdatas = data_list
                    st.session_state.client_log[st.session_state.turn] += "Night Received \n\n"
                    st.session_state.client_log[st.session_state.turn] += '\n\n'.join(data_list)
                    st.session_state.client_log[st.session_state.turn] += '--- \n\n'
                    for data_log in data_list:
                        if ':' in data_log:
                            name, msg = data_log.split(':')
                            st.session_state.message_logdict[name.strip()] += f"{st.session_state.turn}:(received){msg}\n\n"
                    for d in st.session_state.rdatas:
                        if d == "":
                            continue
                        if d.split(':')[0] == 'Messages':
                            st.session_state.rnames.append(d.split(':')[1])
                        else:
                            st.session_state.rnames.append(d.split(':')[0])
                with st.sidebar:
                    st.title(f"📥 {st.session_state.name}'s Message Box")
                    names = st.session_state.status_logdict.keys()
                    names.remove(st.session_state.name)
                    selected = st.radio('Select one to see chats.', names, horizontal=True)
                    if selected in names:
                        st.write(f"endowment: {st.session_state.status_logdict[selected]}")
                        for msgs in st.session_state.message_logdict[selected.strip()].split('\n\n'):
                            if "(received)" in msgs:
                                name, msg = msgs.split("(received)")
                                with st.chat_message(name='assistant', avatar=f'person_images/{selected.strip()}.png'):
                                    st.write(msg)
                            elif "(send)" in msgs:
                                name, msg = msgs.split("(send)")
                                with st.chat_message(name='user', avatar=f'person_images/{st.session_state.name}.png'):
                                    st.write(msg)


        with self.placeholder.container():
            st.markdown("### **Day Secret Mailbox**")

            if st.session_state.rdatas[0] != "":
                st.write("📩 You received messages:")
                for d in st.session_state.rdatas:
                    if d == "":
                        continue
                    if d.split(':')[0] == 'Messages':
                        st.write(f"📧 {d.split(':')[1]}: {d.split(':')[2]}")
                    else:
                        st.write(f"📧 {d.split(':')[0]}: {d.split(':')[1]}")
                dmsgc = st.container()
                dmsgc.write("**Write your reply!**")
                player_msgs = {}
                for rname in st.session_state.rnames:
                    if rname != "":
                        player_msgs[rname] = dmsgc.text_area(f"📧 Reply to {rname}", key=f'tadms{rname}')
                smsg = "📤 Send"
            else:
                st.write("❌ You received no messages.")
                player_msgs = {}
                smsg = "➡️ Next"

            st.button(smsg, key='daysend', on_click=sending_mail, kwargs={'time': 'day', 'player_msgs': player_msgs})

    def game_end_page(self):
        st.write("🎯 The game ends.")
        st.write("Thank you for participate!")
        

        st.button("Goto Interview page", key='button6', on_click=initpage)