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
    for pidx, msg in player_msgs.items():
        pname = st.session_state.player_names[pidx]
        if msg != "":
            sending += f"{pname}@{msg}\n\n" 
    st.session_state.server_socket.send(f'{time}\n\n{sending}END'.encode())
    st.session_state.client_log[st.session_state.turn] += f"{time} Send \n\n"
    st.session_state.client_log[st.session_state.turn] += sending.replace('@', ': ')
    for sends in sending.replace('@', ': ').split('\n\n'):
        if ':' in sends:
            name, msg = sends.split(':')
            emoji = "🌞" if time == 'day' else "🌒"
            st.session_state.message_logdict[name.strip()] += f"{st.session_state.turn}:(send)({st.session_state.turn}-{emoji}) {msg}\n\n"
    st.session_state.client_log[st.session_state.turn] += "\n\n --- \n\n"
    st.session_state.session_control = False
    st.session_state.tmp_submitted = {k:False for k in st.session_state.tmp_submitted.keys()}
    st.session_state.tmp_chat_new_msg = {k:"" for k in st.session_state.tmp_chat_new_msg}
    if time == 'night':
        st.session_state.page += 1
    elif time == 'day':
        turnpage()
 
def write_team_chat_container(con, team, names, disabled):
    fc = con.container()
    cb1, cb2 = con.columns([1,1])
    cb1c = cb1.container(height=600)
    cb3c = cb1.container(height=600)
    cb2c = cb2.container(height=600)
    cb4c = cb2.container(height=600)
    eds = 0
    if team == 'blue':
        eds += write_chat_container(cb1c, names[0], disabled[0], 0)
        eds += write_chat_container(cb3c, names[2], disabled[2], 2)
        eds += write_chat_container(cb2c, names[1], disabled[1], 1)
        eds += write_chat_container(cb4c, names[3], disabled[3], 3)
    else:
        eds += write_chat_container(cb1c, names[4], disabled[4], 4)
        eds += write_chat_container(cb3c, names[6], disabled[6], 6)
        eds += write_chat_container(cb2c, names[5], disabled[5], 5)
        eds += write_chat_container(cb4c, names[7], disabled[7], 7)
    fc.markdown(f"<h3 style='text-align: center; color:{team};'>{team.capitalize()} Team </h3>", unsafe_allow_html=True)
    fc.markdown(f"<p style='text-align: center; '>Total Endowment 💰 {eds}</h1>", unsafe_allow_html=True)
    

def write_chat_container(con, cname, disabled, n):
    cheight = 250
    ncon = con.container()
    concon = con.container(height=cheight, border=False)
    if st.session_state.status_logdict[cname] == "":
        endowment = 1200
    else:
        endowment = st.session_state.status_logdict[cname]
    if cname == st.session_state.name:
        with ncon.chat_message('user', avatar=f'person_images/{st.session_state.name}.png'):
            st.write(f"{cname} (💰: {endowment})")
        #concon.write(f"endowment: {endowment}")
    else:
        with ncon.chat_message('user', avatar=f'person_images/{cname}.png'):
            st.write(f"{cname} (💰: {endowment})")
        #concon.write(f"endowment: {endowment}")
        for msgs in st.session_state.message_logdict[cname].split('\n\n'):
            if "(received)" in msgs:
                name, msg = msgs.split("(received)")
                if '(bot)' in cname:
                    cname = cname.split(' (bot)')[0]
                with concon.chat_message('assistant', avatar=f'person_images/{cname.strip()}.png'):
                    st.write(msg)
            elif "(send)" in msgs:
                name, msg = msgs.split("(send)")
                with concon.chat_message('user', avatar=f'person_images/{st.session_state.name}.png'):
                    st.write(msg)
        with con.form(key=f'sbmit{cname}', border=False):
            st.session_state.tmp_chat_new_msg[n] = st.text_area(label='new message', value=st.session_state.tmp_chat_new_msg[n], key=f"nmsg{cname}", height=30, disabled=disabled)
            submitted = st.form_submit_button("Submit",  disabled=disabled)
            if submitted:
                st.session_state.tmp_submitted[cname] = True
            if st.session_state.tmp_submitted[cname]:
                st.write("Successfully Editted.")
    return int(endowment)

def write_graph(vis_turn):
    while True:
        try:
            contribution_df = pd.DataFrame(st.session_state.contribution_table)
            contribution_df.columns = [name[0] for name in contribution_df.columns]
            contribution_df['turn'] = list(range(0, vis_turn))
            endowment_df = pd.DataFrame(st.session_state.endowment_table)
            endowment_df.columns = [name[0] for name in endowment_df.columns]
            endowment_df['turn'] = list(range(0, vis_turn))
            break
        except Exception as e:
            #print(e)
            continue
        

    st.write("### Graph")
    gselect = st.selectbox("Graph to shown", ["contribution", "endowment"])
    if gselect == 'contribution':
        st.line_chart(contribution_df.set_index('turn'))
    elif gselect == 'endowment':
        st.line_chart(endowment_df.set_index('turn'))


def write_public_messages(vis_turn):
    st.write(f"### Public Messages at Turn {vis_turn}")
    pmsg_con = st.container(border=True, height=500)
    for msgstr in st.session_state.public_messages:
        if ':' in msgstr:
            if len(msgstr.split(':')) > 2:
                n = msgstr.split(':')[0]
                msg = msgstr.split(':')[-1]
            else:
                n, msg = msgstr.split(':')
            if n[0] < 'E':
                msg = f":blue[{n}]: {msg}"
            else:
                msg = f":red[{n}]: {msg}"
            with pmsg_con.chat_message("assistant", avatar=f"person_images/{n.strip()}.png"):
                st.markdown(msg)

class PublicGoodsClient(DefaultClient):
    def __init__(self, placeholder):

        super().__init__(placeholder)
        pass

    def button2(self, **kwargs):
        
        cur_bid = kwargs['cur_bid']
        st.session_state.server_socket.send(f'bid\n\n{cur_bid}'.encode())
        st.session_state.session_control = False
        st.session_state.table_updated = False
        st.session_state.page += 1

    def button3(self, **kwargs):
        pmsg_str = kwargs['public_message']
        if len(kwargs['checkbox']) < 1:
            encoding_str = f"end_turn\n\n{pmsg_str}"
        else:
            checkbox_str = " ".join(["1" if b else "0" for b in kwargs['checkbox']])
            encoding_str = f"end_turn\n\n{pmsg_str}\n\n{checkbox_str}"

        st.session_state.server_socket.send(encoding_str.encode())
        st.session_state.session_control = False
        st.session_state.table_updated = False

        st.session_state.page += 1

    def button4(self, func):
        st.session_state.session_control = False
        func()

    ### page implementations
    def main_page(self, HOST, PORT):
        self.placeholder.markdown(f"<h1 style='text-align: center; '>Public Good Game</h1>", unsafe_allow_html=True)

        _, cp, _ = self.placeholder.columns([3,2,3])
        with cp.container():
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
        self.placeholder.markdown(f"<h1 style='text-align: center; '>Public Good Game</h1>", unsafe_allow_html=True)

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
                                st.session_state.message_logdict[name.strip()] += f"{st.session_state.turn-1}:(received)({st.session_state.turn}-🌞) {msg}\n\n"
        # start turn
        bp, _, cp, _, rp = self.placeholder.columns([4.1,0.1,2.4,0.1,4.1])
        with cp.container():
            data_list = st.session_state.player_data
            st.markdown(f"### Turn {st.session_state.turn} / 8 Bidding.")
            st.markdown(f"👤 **You are {st.session_state.name}.**")
            on = st.toggle(f"Click to see Round Rule.")
            if on:
                st.markdown(f"  -   You need to pay {data_list[2]} fare.")
                st.markdown(f"  -   Project will be success if all contribution is over {data_list[3]}.")
                st.markdown(f"  -   If project success, you will receive an amount distributed according to the number of people, twice the total.")
                st.markdown(f"  -   If project fail, you get nothing.")
                st.markdown(f"  -   For example, if all people bid at least {int(data_list[2]) // 2}, you can deserve all {data_list[2]} fare.")
                st.markdown("   -   Contribute smart to survive 8 rounds!")

            if st.session_state.turn != 1:
                ## graph
                write_graph(st.session_state.turn)

                ## public messages
                write_public_messages(st.session_state.turn-1)

            ## first turn show team info
            else:
                st.markdown(f"#### **Your status**")
                col1, col2 = st.columns(2)
                col1.image(f'person_images/{st.session_state.name}.png')
                col2.write(f"**Name**       : {data_list[0]}")
                #col2.write(f"**Endowment**  : {data_list[1]}")

                other_players_info = data_list[4].split('   ')[:-1]
                team_player_num = len(other_players_info)//2
                if 'tmp_chat_new_msg' not in st.session_state:
                    st.session_state.tmp_chat_new_msg = defaultdict(str)
                if st.session_state.name[0] < 'E':
                    st.markdown(f"### :blue[Blue Team] (YOURS)")
                else:
                    st.markdown(f"### :blue[Blue Team]")
                bcols = st.columns(team_player_num) # TODO: make dynamic

                for i, col in enumerate(bcols):
                    c_name = other_players_info[i].split(':')[0][1:]
                    c_endowment = other_players_info[i].split('- ')[-1].split(' ')[0]
                    col.write(f"{c_name}")
                    if c_name not in st.session_state.status_logdict.keys():
                        st.session_state.status_logdict[c_name] = ""
                    if '(bot)' in c_name:
                        c_name = c_name.split(' (bot)')[0]
                    col.image(f'person_images/{c_name}.png')
                    #col.write(f"**Endowment :** {c_endowment}")
                
                if st.session_state.name[0] > 'D':
                    st.markdown(f"### :red[Red Team] (YOURS)")
                else:
                    st.markdown(f"### :red[Red Team]")
                rcols = st.columns(team_player_num) # TODO: make dynamic

                for i, col in enumerate(rcols):
                    c_name = other_players_info[i+team_player_num].split(':')[0][1:]
                    c_endowment = other_players_info[i+team_player_num].split('- ')[-1].split(' ')[0]
                    col.write(f"{c_name}")
                    if c_name not in st.session_state.status_logdict.keys():
                        st.session_state.status_logdict[c_name] = ""
                    if '(bot)' in c_name:
                        c_name = c_name.split(' (bot)')[0]
                    col.image(f'person_images/{c_name}.png')
                    #col.write(f"**Endowment :** {c_endowment}")
            

            ## Chat interface : TODO dynamic with n, not just 4
            # Blue team
            other_players_info = data_list[4].split('   ')[:-1]
            st.session_state.player_names = list(st.session_state.status_logdict.keys())
            st.session_state.tmp_submitted = {k: False for k in st.session_state.status_logdict.keys()}
            disabled = [True for i in range(len(other_players_info))]
            write_team_chat_container(bp, 'blue', st.session_state.player_names, disabled)
            write_team_chat_container(rp, 'red', st.session_state.player_names, disabled)

            
        
            st.markdown(f"### **Contribution for Turn {st.session_state.turn}**")
            cur_bid = st.number_input("💰 Contribution", min_value=0, max_value=int(data_list[1]), key='bid')
            st.button("🛠️ Bet", key='button2', on_click=self.button2, kwargs={"cur_bid":cur_bid})


    def turn_waiting_page(self):
        self.placeholder.markdown(f"<h1 style='text-align: center; '>Public Good Game</h1>", unsafe_allow_html=True)

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

        bp, _, cp, _, rp = self.placeholder.columns([4.1,0.1,2.4,0.1,4.1])

        ## Chat interface : TODO dynamic with n, not just 4
        # Blue team
        names = st.session_state.player_names
        disabled = [True for i in range(len(names))]

        write_team_chat_container(bp, 'blue', names, disabled)
        write_team_chat_container(rp, 'red', names, disabled)
        with cp:

            col1, col2, col3 = st.columns([1,2,1])
            st.markdown(f"### Turn {st.session_state.turn} Ended.")
            st.markdown(f"### :red[🏦 {data_list[1]}]")
            
            st.markdown("#### **Contribution**")
            # col1, col2 = st.columns(2)
            
            
            other_players_info = data_list[2].split('\n')
            other_players_cont = data_list[3].split('\n')

            team_player_num = len(other_players_info)//2
            st.write(":blue[Blue Team]")
            bcols = st.columns(team_player_num)
            st.write(":red[Red Team]")
            rcols = st.columns(team_player_num)
            total_conts = 0
            for i, pinfo in enumerate(other_players_info):
                c_name = pinfo.split(':')[0].strip()
                c_endowment = pinfo.split(':')[1].strip()
                c_contribution = other_players_cont[i].split(':')[1].strip()
                str_endowment = "\n" + c_endowment
                str_contribution = "\n" + c_contribution
                if not st.session_state.table_updated:
                    if c_name not in st.session_state.contribution_table.keys():
                        st.session_state.contribution_table[c_name] = [0, int(c_contribution)]
                    else:
                        st.session_state.contribution_table[c_name].append(int(c_contribution))
                    if c_name not in st.session_state.endowment_table.keys():
                        st.session_state.endowment_table[c_name] = [1200, int(c_endowment)] # TODO: dynamic init endo
                    else:
                        st.session_state.endowment_table[c_name].append(int(c_endowment))
                    total_conts += int(c_contribution)
                
                if i < team_player_num:
                    col = bcols[i]
                else:
                    col = rcols[i-team_player_num]
                col.write(f"{c_name}")
                if '(bot)' in c_name:
                    c_name = c_name.split(' (bot)')[0]
                col.image(f'person_images/{c_name}.png')
                col.markdown(f"💸 {str_contribution}")
                # if len(st.session_state.checkboxs) == len(cols):
                #     if c_name == st.session_state.name:
                #         st.session_state.checkboxs[i] = cols[i].checkbox(f"Me", value=st.session_state.checkboxs[i], key=f'ch{i}', disabled=True)
                #     else:
                #         st.session_state.checkboxs[i] = cols[i].checkbox(f"Is he(she) AI?", value=st.session_state.checkboxs[i], key=f'ch{i}')
            
            if not st.session_state.table_updated:
                st.session_state.tmp_conts = total_conts//8 if "succeed" in data_list[1] else 0
            st.session_state.table_updated = True
            st.write(f"You've got ➕ 💰{st.session_state.tmp_conts}.")
            st.write(f"You've paid ➖ 💰 300 fare.")

            ## graph
            write_graph(st.session_state.turn+1)

            ## public messages
            if st.session_state.turn > 1:
                write_public_messages(st.session_state.turn-1)

            tmp_keys = list(st.session_state.endowment_table.keys()).copy()
            for k in tmp_keys:
                if k in st.session_state.endowment_table.keys():
                    if st.session_state.endowment_table[k][-1] <= 0:
                        st.session_state.contribution_table.pop(k, None)
                        st.session_state.endowment_table.pop(k, None)
            onclick = self.button3
            if data_list[4] != 'none':
                st.write('\n\n'.join(data_list[4].split('\n')))

                if cur_ed <= 0:
                    st.write("❌ You have been eliminated.")
                    onclick = endpage
                    public_message = ""

            if onclick != endpage:
                st.write("### Write Public Message")
                on = st.toggle(f"Click to see Message Rule.")
                if on:
                    st.write("  -   You can write message as Korean, but please avoid using abbreviations or slang if possible. ")
                    st.write("  -   Your message will be translated, proofread and delivered in English to opponents.")
                    st.write("  -   Also, please do not use double enter in your message.")
                public_message = st.text_area("📧 Public Message", key='publics')
                st.button("➡️ End Turn", key='button3', on_click=onclick, kwargs={"checkbox": st.session_state.checkboxs, "public_message": public_message})
            else:
                st.button("➡️ End Turn", key='button3', on_click=onclick)


    def turn_end_page(self):
        self.placeholder.markdown(f"<h1 style='text-align: center; '>Public Good Game</h1>", unsafe_allow_html=True)

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
        self.placeholder.markdown(f"<h1 style='text-align: center; '>Public Good Game</h1>", unsafe_allow_html=True)

        with self.placeholder:
            with st.spinner("🌒 Waiting for the server to start night..."):
                if not st.session_state.session_control:
                    data = ""
                    while 'STP' not in data:
                        buf = st.session_state.server_socket.recv(1024)
                        data = buf.decode('utf-8')
                    if len(buf) == 1024:
                        while buf[-3:] != b'END':
                            buf += st.session_state.server_socket.recv(1024)
                        data = buf[:-3].decode('utf-8')
                    public_messages = data.split('STP')[-1].split('\n\n')
                    st.session_state.public_messages = public_messages
                    st.session_state.server_socket.send('received'.encode())
                    st.session_state.session_control = True
                    st.session_state.server_socket.send('get_player_name'.encode())
                    while 'player_name' not in data:
                        data = st.session_state.server_socket.recv(1024).decode('utf-8')
                    pname_list = data.split('player_name')[-1].split('\n')
                    pname_list = [item.replace("start", "") for item in pname_list if item != 'start']
                    st.session_state.pname_list = pname_list
            
        
        bp, _, cp, _, rp = self.placeholder.columns([4.1,0.1,2.4,0.1,4.1])
        ## Chat interface : TODO dynamic with n, not just 4
        # Blue team
        names = st.session_state.player_names
        disabled = [False if name in list(st.contribution_table.keys()) else True for name in names]

        write_team_chat_container(bp, 'blue', names, disabled)
        write_team_chat_container(rp, 'red', names, disabled)

        with cp.container():

            st.markdown(f"### 🌒 **Turn {st.session_state.turn} Night Mailbox**")

            ## graph
            write_graph(st.session_state.turn)

            ## public messages
            write_public_messages(st.session_state.turn)

                    
            st.write("### Write secret message")
            on = st.toggle(f"Click to see Message Rule.")
            if on:
                st.write("  -   You can write message as Korean, but please avoid using abbreviations or slang if possible.")
                st.write("  -   Your message will be translated, proofread and delivered in English to opponents.")
                st.write("  -   Also, please do not use double enter in your message.")
            
            st.write("**If you have completed writing the message, click the checkbox and then click the Send button.**")
        
            checked = st.checkbox('Done!', key = f'ch')
            st.button('📤 Send', on_click=sending_mail, kwargs={'time':'night','player_msgs': st.session_state.tmp_chat_new_msg}, disabled = not checked)
    
    def day_msg_page(self):
        self.placeholder.markdown(f"<h1 style='text-align: center; '>Public Good Game</h1>", unsafe_allow_html=True)
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
                            st.session_state.message_logdict[name.strip()] += f"{st.session_state.turn}:(received)({st.session_state.turn}-🌒){msg}\n\n"
                    for d in st.session_state.rdatas:
                        if d == "" or d == "END":
                            continue
                        if d.split(':')[0] == 'Messages':
                            st.session_state.rnames.append(d.split(':')[1].strip())
                        else:
                            st.session_state.rnames.append(d.split(':')[0].strip())
            
        bp, _, cp, _, rp = self.placeholder.columns([4.1,0.1,2.4,0.1,4.1])
        ## Chat interface : TODO dynamic with n, not just 4
        # Blue team
        names = st.session_state.player_names
        disabled = [False if name in st.session_state.rnames else True for name in names]
        write_team_chat_container(bp, 'blue', names, disabled)
        write_team_chat_container(rp, 'red', names, disabled)

        with cp.container():
            st.markdown(f"### 🌞 **Turn {st.session_state.turn} Day Mailbox**")

            ## graph
            write_graph(st.session_state.turn)

            ## public messages
            write_public_messages(st.session_state.turn)

            st.write("### Write replys")
            if st.session_state.rdatas[0] != "":
                st.write("📩 You've got messages from:")
                cols = st.columns(len(st.session_state.rnames))
                for i, col in enumerate(cols):
                    col.write(st.session_state.rnames[i])
                    col.image(f'person_images/{st.session_state.rnames[i]}.png', width=100)
                on = st.toggle(f"Click to see Message Rule.")
                if on:
                    st.write("  -   You can write message as Korean, but please avoid using abbreviations or slang if possible.")
                    st.write("  -   Your message will be translated, proofread and delivered in English to opponents.")
                    st.write("  -   Also, please do not use double enter in your message.")
            else:
                st.write("❌ You've got no messages.")
                st.write("Just press Send button.")
            
            st.write("**If you have completed writing the message, click the checkbox and then click the Send button.**")
            
            checked2 = st.checkbox('Done!', key = f'ch2')
            st.button('📤 Send', key='daysend', on_click=sending_mail, kwargs={'time': 'day','player_msgs': st.session_state.tmp_chat_new_msg}, disabled = not checked2)


    def game_end_page(self):
        st.write("🎯 The game ends.")
        st.write("Thank you for participate!")
        

        st.button("Goto Interview page", key='button6', on_click=initpage)