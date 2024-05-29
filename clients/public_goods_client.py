from .default_client import *
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import copy

def initpage():
    st.session_state.page = 0
def endpage():
    st.session_state.page = 4
def msgpage():
    st.session_state.page = 5
def change_value(v):
    return not v

def sending_mail(player_msgs, time):
    sending = ""
    for pname, msg in player_msgs.items():
        if msg != "":
            sending += f"{pname}@{msg}\n\n" 
    st.session_state.server_socket.send(f'{time}\n\n{sending}END'.encode())
    st.session_state.client_log[st.session_state.turn] += f"{time} Send \n\n"
    st.session_state.client_log[st.session_state.turn] += sending.replace('@', ': ')
    for sends in sending.replace('@', ': ').split('\n\n'):
        if ':' in sends:
            name, msg = sends.split(':')
            st.session_state.message_logdict[name.strip()] += f"{st.session_state.turn}:(send)({time} {st.session_state.turn}) {msg}\n\n"
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
        st.session_state.server_socket.send(f'bid\n\n{cur_bid}'.encode())
        st.session_state.session_control = False
        st.session_state.page += 1

    def button3(self, **kwargs):
        pmsg_str = kwargs['public_message']
        if len(kwargs['checkbox']) < 1:
            encoding_str = f"end_turn\n\n{pmsg_str}"
        else:
            checkbox_str = " ".join(["1" if b else "0" for b in kwargs['checkbox']])
            encoding_str = f"end_turn\n\n{pmsg_str}\n\n{checkbox_str}"

        st.session_state.contribution_table = kwargs['contribution_table']
        st.session_state.endowment_table = kwargs['endowment_table']
        st.session_state.server_socket.send(encoding_str.encode())
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
            HOST = st.text_input('🌐 IP Address', value='127.0.0.1')
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
                        buf = st.session_state.server_socket.recv(1024)
                        data = buf.decode('utf-8')
                    if len(buf) == 1024:
                        while buf[-3:] != b'END':
                            buf += st.session_state.server_socket.recv(1024)
                        data = buf[:-3].decode('utf-8')
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
                                st.session_state.message_logdict[name.strip()] += f"{st.session_state.turn-1}:(received)(day {st.session_state.turn}) {msg}\n\n"
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
                if '(bot)' in c_name:
                    c_name = c_name.split(' (bot)')[0]
                col.image(f'person_images/{c_name}.png')
                col.write(f"**Endowment :** {c_endowment}")
            
            if st.session_state.turn > 1:
                with st.sidebar:
                    st.image(f'person_images/{st.session_state.name}.png', width=100)
                    st.title(f"📥 {st.session_state.name}'s Message Box")
                    names = list(st.session_state.status_logdict.keys())
                    names.remove(st.session_state.name)
                    selected = st.radio('Select one to see chats.', names, horizontal=True)
                    if selected in names:
                        st.write(f"endowment: {st.session_state.status_logdict[selected]}")
                        for msgs in st.session_state.message_logdict[selected.strip()].split('\n\n'):
                            if "(received)" in msgs:
                                name, msg = msgs.split("(received)")
                                if '(bot)' in selected:
                                    selected = selected.split(' (bot)')[0]
                                with st.chat_message('assistant', avatar=f'person_images/{selected.strip()}.png'):
                                    st.write(msg)
                            elif "(send)" in msgs:
                                name, msg = msgs.split("(send)")
                                with st.chat_message('user', avatar=f'person_images/{st.session_state.name}.png'):
                                    st.write(msg)

            st.markdown(f"### **Contribution for Turn {st.session_state.turn}**")
            cur_bid = st.number_input("💰 Contribution", min_value=0, max_value=int(data_list[1]), key='bid')
            st.button("🛠️ Bet", key='button2', on_click=self.button2, kwargs={"cur_bid":cur_bid})


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
                    if 'None' not in data_list[4]:
                        st.session_state.checkboxs = [True if b == '1' else False for b in data_list[5].split(' ')]
                    else:
                        st.session_state.checkboxs = []
                    endo_str = '  '.join(endo_splits)
                    cont_str = '  '.join(cont_splits)
                    st.session_state.client_log[st.session_state.turn] = f"**Endowment**\n\n{endo_str}\n\n**Contribution**\n\n{cont_str}\n\n --- \n\n"+ st.session_state.client_log[st.session_state.turn]
                    for i in range(len(endo_splits)):
                        if ':' in endo_splits[i]:
                            name, endo = endo_splits[i].split(':') 
                            st.session_state.status_logdict[name.strip()] = endo

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
            other_players_info = data_list[2].split('\n')
            other_players_cont = data_list[3].split('\n')

            
            cols = st.columns(len(other_players_info))
            contribution_table = copy.deepcopy(st.session_state.contribution_table)
            endowment_table = copy.deepcopy(st.session_state.endowment_table)
            for i, pinfo in enumerate(other_players_info):
                c_name = pinfo.split(':')[0].strip()
                c_endowment = pinfo.split(':')[1].strip()
                c_contribution = other_players_cont[i].split(':')[1].strip()
                str_endowment = "\n" + c_endowment
                str_contribution = "\n" + c_contribution
                if c_name not in contribution_table.keys():
                    contribution_table[c_name] = [0, int(c_contribution)]
                else:
                    contribution_table[c_name].append(int(c_contribution))
                if c_name not in endowment_table.keys():
                    endowment_table[c_name] = [1200, int(c_endowment)] # TODO: dynamic init endo
                else:
                    endowment_table[c_name].append(int(c_endowment))
                
                

                cols[i].write(f"{c_name}")
                if '(bot)' in c_name:
                    c_name = c_name.split(' (bot)')[0]
                cols[i].image(f'person_images/{c_name}.png')
                cols[i].markdown(f"**Contribution**  {str_contribution}")
                cols[i].markdown(f"**Endowment**   {str_endowment}")
                if len(st.session_state.checkboxs) == len(cols):
                    if c_name == st.session_state.name:
                        st.session_state.checkboxs[i] = cols[i].checkbox(f"Me", value=st.session_state.checkboxs[i], key=f'ch{i}', disabled=True)
                    else:
                        st.session_state.checkboxs[i] = cols[i].checkbox(f"Is he(she) AI?", value=st.session_state.checkboxs[i], key=f'ch{i}')
            
            tmp_keys = list(endowment_table.keys()).copy()
            for k in tmp_keys:
                if k in endowment_table.keys():
                    if endowment_table[k][-1] <= 0:
                        contribution_table.pop(k, None)
                        endowment_table.pop(k, None)
            onclick = self.button3
            if data_list[4] != 'none':
                st.write('\n\n'.join(data_list[4].split('\n')))

                if cur_ed <= 0:
                    st.write("❌ You have been eliminated.")
                    onclick = endpage
                    public_message = ""

            if onclick != endpage:
                st.write("---")
                st.write("Write message to public!")
                st.write("  -   You can write message as Korean, but please avoid using abbreviations or slang if possible. ")
                st.write("  -   Your message will be translated, proofread and delivered in English to opponents.")
                st.write("  -   Also, please do not use double enter in your message.")
                public_message = st.text_area("📧 Public Message", key='publics')
                st.button("➡️ End Turn", key='button3', on_click=onclick, kwargs={"checkbox": st.session_state.checkboxs, "public_message": public_message, "contribution_table": contribution_table, "endowment_table": endowment_table})
            else:
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
                        buf = st.session_state.server_socket.recv(1024)
                        data = buf.decode('utf-8')
                    if len(buf) == 1024:
                        while buf[-3:] != b'END':
                            buf += st.session_state.server_socket.recv(1024)
                        data = buf[:-3].decode('utf-8')
                    public_messages = 'start'.join(data.split('start')[1:]).split('\n\n')
                    st.session_state.public_messages = public_messages
                    st.session_state.server_socket.send('received'.encode())
                    st.session_state.session_control = True
                    st.session_state.server_socket.send('get_player_name'.encode())
                    while 'player_name' not in data:
                        data = st.session_state.server_socket.recv(1024).decode('utf-8')
                    pname_list = data.split('player_name')[-1].split('\n')
                    pname_list = [item.replace("start", "") for item in pname_list if item != 'start']
                    st.session_state.pname_list = pname_list
            

        
        with self.placeholder.container():
            with st.sidebar:
                st.image(f'person_images/{st.session_state.name}.png', width=100)
                st.title(f"📥 {st.session_state.name}'s Message Box")
                names = list(st.session_state.status_logdict.keys())
                names.remove(st.session_state.name)
                selected = st.radio('Select one to see chats.', names, horizontal=True)
                if selected in names:
                    st.write(f"endowment: {st.session_state.status_logdict[selected]}")
                    for msgs in st.session_state.message_logdict[selected.strip().strip()].split('\n\n'):
                        if "(received)" in msgs:
                            name, msg = msgs.split("(received)")
                            if '(bot)' in selected:
                                selected = selected.split(' (bot)')[0]
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
            st.write("  -   Also, please do not use double enter in your message.")
        
            while True:
                try:
                    contribution_df = pd.DataFrame(st.session_state.contribution_table)
                    contribution_df.columns = [name[0] for name in contribution_df.columns]
                    contribution_df['turn'] = list(range(0, st.session_state.turn))
                    endowment_df = pd.DataFrame(st.session_state.endowment_table)
                    endowment_df.columns = [name[0] for name in endowment_df.columns]
                    endowment_df['turn'] = list(range(0, st.session_state.turn))
                    break
                except Exception as e:
                    #print(e)
                    for c_name in st.session_state.contribution_table.keys():
                        if len(st.session_state.contribution_table[c_name]) > st.session_state.turn:
                            st.session_state.contribution_table[c_name].pop()
                    for c_name in st.session_state.endowment_table.keys():
                        if len(st.session_state.endowment_table[c_name]) > st.session_state.turn:
                            st.session_state.endowment_table[c_name].pop()
                    continue
                    
            
            col1, col2 = st.columns(2)
            col1.write("Contributions")
            col1.line_chart(contribution_df.set_index('turn'))
            col2.write("Endowments")
            col2.line_chart(endowment_df.set_index('turn'))
            st.write('---')
            col1, col2 = st.columns([0.9, 0.1])
            pmsg_list = {}
            for msgstr in st.session_state.public_messages:
                if ':' in msgstr:
                    if len(msgstr.split(':')) > 2:
                        n = msgstr.split(':')[0]
                        msg = msgstr.split(':')[-1]
                    else:
                        n, msg = msgstr.split(':')
                    pmsg_list[n] = msg

            player_msgs = {}
            with col1.form(key='nightmsg'):
                
                for i, pname in enumerate(st.session_state.pname_list):
                    if pname == st.session_state.name or pname.strip() == "":
                        continue
                    if len(st.session_state.contribution_table[pname.strip()]) == st.session_state.turn:
                        st.write(f"📡 Public Messages from {pname}")
                        if pmsg_list[pname].strip() == "":
                            st.write("❌ No public message.")
                        else:
                            cc = st.container(border=True)
                            cc.write(pmsg_list[pname])
                        player_msgs[pname] = st.text_area(f"📧 Message to {pname}", key=f"nmsg{i}")
                nightmsg_btn = st.form_submit_button('Form update')
                
            if nightmsg_btn:
                col2.button('📤 Send', on_click=sending_mail, kwargs={'time':'night','player_msgs': player_msgs})
    
    def day_msg_page(self):
        with self.placeholder:
            with st.spinner("🌞 Waiting for the server to start day..."):
                if not st.session_state.session_control:
                    data = ""
                    while 'reply' not in data:
                        buf = st.session_state.server_socket.recv(1024)
                        data = buf.decode('utf-8')
                    if len(buf) == 1024:
                        while buf[-3:] != b'END':
                            buf += self.client.recv(1024)
                        data = buf[:-3].decode('utf-8')
                    
                    data_list = 'replys'.join(data.split('replys')[1:]).split('\n\n')
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
                            st.session_state.message_logdict[name.strip()] += f"{st.session_state.turn}:(received)(night {st.session_state.turn}){msg}\n\n"
                    for d in st.session_state.rdatas:
                        if d == "" or d == "END":
                            continue
                        if d.split(':')[0] == 'Messages':
                            st.session_state.rnames.append(d.split(':')[1])
                        else:
                            st.session_state.rnames.append(d.split(':')[0])
            with st.sidebar:
                st.image(f'person_images/{st.session_state.name}.png', width=100)
                st.title(f"📥 {st.session_state.name}'s Message Box")
                names = list(st.session_state.status_logdict.keys())
                names.remove(st.session_state.name)
                selected = st.radio('Select one to see chats.', names, horizontal=True)
                if selected in names:
                    st.write(f"endowment: {st.session_state.status_logdict[selected]}")
                    for msgs in st.session_state.message_logdict[selected.strip()].split('\n\n'):
                        if "(received)" in msgs:
                            name, msg = msgs.split("(received)")
                            if '(bot)' in selected:
                                selected = selected.split(' (bot)')[0]
                            with st.chat_message(name='assistant', avatar=f'person_images/{selected.strip()}.png'):
                                st.write(msg)
                        elif "(send)" in msgs:
                            name, msg = msgs.split("(send)")
                            with st.chat_message(name='user', avatar=f'person_images/{st.session_state.name}.png'):
                                st.write(msg)


        with self.placeholder.container():
            st.markdown("### 🌞 **Day Secret Mailbox**")

            if st.session_state.rdatas[0] != "":
                st.write("📩 You received messages:")
                for d in st.session_state.rdatas:
                    if d == "" or d == "END":
                        continue
                    if d.split(':')[0] == 'Messages':
                        st.write(f"📧 {d.split(':')[1]}: {d.split(':')[2]}")
                    else:
                        st.write(f"📧 {d.split(':')[0]}: {d.split(':')[1]}")
                
                col1, col2 = st.columns([0.9, 0.1])
                with col1.form(key='dayform'):
                    dmsgc = st.container()
                    dmsgc.write("**Write your reply!**")
                    player_msgs = {}
                    for rname in st.session_state.rnames:
                        if rname != "":
                            player_msgs[rname] = dmsgc.text_area(f"📧 Reply to {rname}", key=f'tadms{rname}')
                    smsg = "📤 Send"
                    dayform_btn = st.form_submit_button('Form update')
                if dayform_btn:
                    col2.button(smsg, key='daysend', on_click=sending_mail, kwargs={'time': 'day', 'player_msgs': player_msgs})

            else:
                st.write("❌ You received no messages.")
                player_msgs = {}
                smsg = "➡️ Next"

                st.button(smsg, key='daysend', on_click=sending_mail, kwargs={'time': 'day', 'player_msgs': player_msgs})

    def game_end_page(self):
        st.write("🎯 The game ends.")
        st.write("Thank you for participate!")
        

        st.button("Goto Interview page", key='button6', on_click=initpage)