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
    st.session_state.client_log[st.session_state.turn] += sending.replace('@', ': ')
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
            HOST = st.text_input('🌐 IP Address', '')
            username = st.text_input('📛 Your Name', '')
            st.write("You will receive a new nickname when the game starts.")
            # persona = st.text_area('Persona', '')
            user_info = {
                "username": username
            }
            st.button("🔗 Connect", key='button1', on_click=button1, kwargs={'HOST': HOST, 'PORT': PORT, 'user_info': user_info}, disabled=st.session_state.page!=0)

    def turn_page(self):
        self.placeholder.write("⌛ Please wait until the server starts the turn.")
            
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
                if len(st.session_state.player_data) > 5:
                    dindex = -1
                    for i, d in enumerate(st.session_state.player_data):
                        if "Replys" in d:
                            dindex = i
                            break
                    
                    st.session_state.client_log[st.session_state.turn] += "\n\nday Received \n\n"
                    if dindex != -1:
                        print(st.session_state.player_data[dindex])
                        st.session_state.client_log[st.session_state.turn] += '\n\n'.join(st.session_state.player_data[dindex:])
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
                st.markdown("   -   Contribute smart to survive 8 rounds!")

            st.markdown(f"#### **Your status**")
            col1, col2 = st.columns(2)
            col1.image(f'person_images/{st.session_state.name}.png')
            col2.write(f"**Name**       : {data_list[0]}")
            col2.write(f"**Endowment**  : {data_list[1]}")

            cols = st.columns(6) # TODO: make dynamic
            other_players_info = data_list[4].split('   ')[:-1]
            for i, col in enumerate(cols):
                c_name = other_players_info[i].split(':')[0][1:]
                c_endowment = other_players_info[i].split('- ')[-1].split(' ')[0]
                col.write(f"{c_name}")
                col.image(f'person_images/{c_name}.png')
                col.write(f"**Endowment :** {c_endowment}")
            
            if st.session_state.turn > 1:
                with st.sidebar:
                    st.title(f"📥 {st.session_state.name}'s Message Box")
                    tab_list = st.tabs([f"Turn {i}" for i in reversed(range(1, st.session_state.turn+1))])
                    for i in range(1, st.session_state.turn+1):
                        with tab_list[i-1]:
                            st.write(st.session_state.client_log[st.session_state.turn+1 -i])

            st.markdown(f"### **Contribution for Turn {st.session_state.turn}**")
            cur_bid = st.number_input("💰 Contribution", min_value=0, max_value=int(data_list[1]))
            st.button("🛠️ Bet", key='button2', on_click=self.button2, kwargs={'cur_bid': cur_bid}, disabled=st.session_state.page != 1)
    
    def turn_waiting_page(self):
        self.placeholder.write("⌛ Waiting for other players to finish betting...")
        
        if not st.session_state.session_control:
            data = ""
            while 'end_turn' not in data:
                data = st.session_state.server_socket.recv(1024).decode('utf-8')
            data_list = data.split('\n\n')
            st.session_state.server_socket.send('received'.encode())
            st.session_state.session_control = True
            st.session_state.player_data = data
            endo_str = '  '.join(data_list[2].split('\n'))
            cont_str = '  '.join(data_list[3].split('\n'))
            st.session_state.client_log[st.session_state.turn] = f"**Endowment**\n\n{endo_str}\n\n**Contribution**\n\n{cont_str}\n\n --- \n\n"+ st.session_state.client_log[st.session_state.turn]
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
                c_endowment = "\n" + other_players_info[i].split(':')[1].strip()
                c_contribution = "\n" + other_players_cont[i].split(':')[1].strip()
                col.write(f"{c_name}")
                col.image(f'person_images/{c_name}.png')
                col.markdown(f"**Contribution**  {c_contribution}")
                col.markdown(f"**Endowment**   {c_endowment}")
                
                
            onclick = self.button3
            if data_list[4] != 'none':
                st.write('\n\n'.join(data_list[4].split('\n')))

                if cur_ed < 0:
                    st.write("❌ You have been eliminated.")
                    onclick = endpage

            st.button("➡️ End Turn", key='button3', on_click=onclick)


    def turn_end_page(self):
        self.placeholder.write("⌛ Waiting for other players to finish checking results...")
        
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
        self.placeholder.write("🌒 Waiting for the server to start night...")
        
        
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
            pname_list = [item for item in pname_list if item != 'start']
            st.session_state.pname_list = pname_list
        if st.session_state.turn > 1:
            with st.sidebar:
                st.title(f"📥 {st.session_state.name}'s Message Box")
                tab_list = st.tabs([f"Turn {i}" for i in reversed(range(1, st.session_state.turn))])
                for i in range(1, st.session_state.turn):
                    with tab_list[i-1]:
                        st.markdown(st.session_state.client_log[st.session_state.turn - i])
        
        with self.placeholder.container():
            st.markdown("### 🌒 **Night Secret Mailbox**")
            st.write("Write secret messages to other players!")
            
            player_msgs = {}
            for pname in st.session_state.pname_list:
                if pname == st.session_state.name or pname == "":
                    continue
                player_msgs[pname] = st.text_area(f"📧 Message to {pname}")
            
            st.button('📤 Send', key='nightsend', on_click=sending_mail, kwargs={'time':'night', 'player_msgs': player_msgs})
        
    
    def day_msg_page(self):
        self.placeholder.write("🌞 Waiting for the server to start day...")
        

        
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
            for d in st.session_state.rdatas:
                if d == "":
                    continue
                if d.split(':')[0] == 'Messages':
                    st.session_state.rnames.append(d.split(':')[1])
                else:
                    st.session_state.rnames.append(d.split(':')[0])
        if st.session_state.turn > 1:
            with st.sidebar:
                st.title(f"📥 {st.session_state.name}'s Message Box")
                tab_list = st.tabs([f"Turn {i}" for i in reversed(range(1, st.session_state.turn+1))])
                for i in range(1, st.session_state.turn+1):
                    with tab_list[i-1]:
                        st.write(st.session_state.client_log[st.session_state.turn+1 - i])

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