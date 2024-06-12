from .default_client import *
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import copy
import plotly.graph_objs as go


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
        if msg != "" and msg is not None:
            msg = msg.replace(":", "")
            sending += f"{pname}@{msg}\n\n" 
    st.session_state.server_socket.send(f'{time}\n\n{sending}END'.encode())
    st.session_state.client_log[st.session_state.turn] += f"{time} Send \n\n"
    st.session_state.client_log[st.session_state.turn] += sending.replace('@', ': ')
    for sends in sending.replace('@', ': ').split('\n\n'):
        if ':' in sends:
            name, msg = sends.split(':')
            emoji = ":green[◀️답장]" if time == 'day' else ":orange[◀️제안]"
            st.session_state.message_logdict[name.strip()] += f"{st.session_state.turn}:(send)**&#x{2459 + st.session_state.turn}; | {emoji}** | {msg}\n\n"
    st.session_state.client_log[st.session_state.turn] += "\n\n --- \n\n"
    st.session_state.session_control = False
    st.session_state.tmp_submitted = {k:False for k in st.session_state.tmp_submitted.keys()}
    st.session_state.tmp_chat_new_msg = {k:"" for k in st.session_state.tmp_chat_new_msg}
    if time == 'night':
        st.session_state.page += 1
    elif time == 'day':
        turnpage()

def get_msg_from_server(splitter):
    data = ""
    buf = b''
    if isinstance(splitter, list):
        bools = sum([sp in data for sp in splitter]) > 0
        while not bools:
            buf += st.session_state.server_socket.recv(1024)
            try:
                data = buf.decode('utf-8')
            except Exception as e:
                print(e)
                bools = sum([sp in data for sp in splitter]) > 0
                continue
            for sp in splitter:
                if sp in data:
                    if 'END' in data:
                        data = sp + data.split(sp)[1].split('END')[0]
                        break
                    else:
                        buf = data.split(sp)[1].encode()
                        st.write(buf)
                        bools = sum([sp in data for sp in splitter]) > 0
                        continue
            bools = sum([sp in data for sp in splitter]) > 0
    else:
        while splitter not in data:
            buf += st.session_state.server_socket.recv(1024)
            try:
                data = buf.decode('utf-8')
            except:
                continue
            if splitter in data:
                data = data.split(splitter)[1]
                if 'END' in data:
                    data = splitter + data.split('END')[0]
                    break
                else:
                    buf = data.encode()
                    continue

    return data

 
def write_team_chat_container(con, team, names, disabled, time):
    fc = con.container()
    cb1, cb2 = con.columns([1,1])
    cb1c = cb1.container(height=700)
    cb3c = cb1.container(height=700)
    cb2c = cb2.container(height=700)
    cb4c = cb2.container(height=700)
    eds = 0
    if team == 'blue':
        eds += write_chat_container(cb1c, names[0], disabled[0], 0, time)
        eds += write_chat_container(cb3c, names[2], disabled[2], 2, time)
        eds += write_chat_container(cb2c, names[1], disabled[1], 1, time)
        eds += write_chat_container(cb4c, names[3], disabled[3], 3, time)
    else:
        eds += write_chat_container(cb1c, names[4], disabled[4], 4, time)
        eds += write_chat_container(cb3c, names[6], disabled[6], 6, time)
        eds += write_chat_container(cb2c, names[5], disabled[5], 5, time)
        eds += write_chat_container(cb4c, names[7], disabled[7], 7, time)
    fc.markdown(f"<h3 style='text-align: center; color:{team};'>{team.capitalize()} Team </h3>", unsafe_allow_html=True)
    fc.markdown(f"<p style='text-align: center; '>팀 자금 총합 💰 {eds}</h1>", unsafe_allow_html=True)
    

def write_chat_container(con, cname, disabled, n, time):
    cheight = 350 if cname != st.session_state.name else 500
    ncon = con.container()
    concon = con.container(height=cheight, border=False)
    
    if '(bot)' in cname:
        iname = cname.split(' (bot)')[0]
    else:
        iname = cname
    if st.session_state.status_logdict[cname] == "":
        endowment = 1200
    else:
        endowment = st.session_state.status_logdict[cname]
    
    if cname == st.session_state.name:
        with ncon.chat_message('user', avatar=f'person_images/{st.session_state.name}.png'):
            st.write(f"{cname} (💰: {endowment})")
        concon.write("### 당신의 캐릭터")
        concon.image(f'person_images/{st.session_state.name}.png')
        #concon.write(f"endowment: {endowment}")
    else:
        if int(endowment) <= 0:
            with ncon.chat_message('user', avatar=f'person_images/{iname}.png'):
                # st.write(f"{cname} (❌ eliminated.)")
                st.write(f"플레이어 {cname} 탈락.")
        else:
            with ncon.chat_message('user', avatar=f'person_images/{iname}.png'):
                st.write(f"{cname} (💰: {endowment})")
        #concon.write(f"endowment: {endowment}")
        for msgs in st.session_state.message_logdict[cname].split('\n\n'):
            if "(received)" in msgs:
                name, msg = msgs.split("(received)")
                with concon.chat_message('assistant', avatar=f'person_images/{iname.strip()}.png'):
                    st.write(msg)
            elif "(send)" in msgs:
                name, msg = msgs.split("(send)")
                with concon.chat_message('user', avatar=f'person_images/{st.session_state.name}.png'):
                    st.write(msg)
        with con.form(key=f'sbmit{cname}', border=False):
            st.session_state.tmp_chat_new_msg[n] = st.text_area(label='new message', value=None, key=f"nmsg{cname}_{time}_{st.session_state.turn}", height=30, disabled=disabled)
            submitted = st.form_submit_button("Submit",  disabled=disabled)
            if submitted:
                st.session_state.tmp_submitted[cname] = True
            if st.session_state.tmp_submitted[cname]:
                # st.write("Successfully Editted.")
                st.write("메시지 작성 완료")
    return int(endowment) if int(endowment) >= 0 else 0

def write_graph(vis_turn):
    while True:
        try:
            contribution_df = pd.DataFrame(st.session_state.contribution_table)
            contribution_df['turn'] = list(range(0, vis_turn))
            endowment_df = pd.DataFrame(st.session_state.endowment_table)
            endowment_df['turn'] = list(range(0, vis_turn))
            break
        except Exception as e:
            continue

    gselect = st.selectbox("입찰 금액 / 자금 그래프 선택", ["플레이어 입찰 금액", "플레이어 자금"])
    
    # Define colors for teams
    red_team_colors = ['#FF0000', '#FF4D4D', '#FF6666', '#FF9999']
    blue_team_colors = ['#0000FF', '#4D4DFF', '#6666FF', '#9999FF']
    team_colors = red_team_colors + blue_team_colors
    
    if gselect == '플레이어 입찰 금액':
        fig = go.Figure()
        for idx, col in enumerate(contribution_df.columns[:-1]):  # Exclude the 'turn' column
            fig.add_trace(go.Scatter(
                x=contribution_df['turn'],
                y=contribution_df[col],
                mode='lines',
                name=col,
                line=dict(width=2, color=team_colors[idx]),  # Set line width and color
                hoverinfo='x+y+name',
            ))
        fig.update_layout(
            title='플레이어 입찰 금액',
            xaxis_title='라운드',
            yaxis_title='금액',
            autosize=True,
            hovermode='x unified',  # Highlight entire line on hover
            xaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=1  # Display integers only
            ),
        )
        st.plotly_chart(fig)
    
    elif gselect == '플레이어 자금':
        fig = go.Figure()
        for idx, col in enumerate(endowment_df.columns[:-1]):  # Exclude the 'turn' column
            fig.add_trace(go.Scatter(
                x=endowment_df['turn'],
                y=endowment_df[col],
                mode='lines',
                name=col,
                line=dict(width=2, color=team_colors[idx]),  # Set line width and color
                hoverinfo='x+y+name',
            ))
        fig.update_layout(
            title='플레이어 자금',
            xaxis_title='라운드',
            yaxis_title='금액',
            hovermode='x unified',  # Highlight entire line on hover
            xaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=1  # Display integers only
            ),
        )
        st.plotly_chart(fig)

def write_public_messages(vis_turn):
    # st.write(f"### Public Messages at Turn {vis_turn}")
    st.write(f"### 이전 라운드 전체 메시지")
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
            if '(bot)' in n:
                n = n.split(' (bot)')[0]
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
        with self.placeholder.container():
            st.markdown(f"<h1 style='text-align: center; '>Public Goods Game</h1>", unsafe_allow_html=True)

        _, cp, _ = self.placeholder.columns([1,2,1])
        with cp.container():
            # st.markdown("### 🎮 Welcome to the New Game!")
            st.markdown("### 🎮 새로운 게임에 오신 것을 환영합니다!")

            # st.write("Type your information and connect to your server!")
            st.write("정보를 입력하시면 서버에 연결해드리겠습니다!")
            HOST = st.text_input('🌐 IP Address', value='13.125.250.236')
            PORT = st.text_input('🌐 PORT', value=20912)
            # username = st.text_input('📛 Your Name', '')
            username = st.text_input('📛 성함', '')
            # st.write("You will receive a new nickname when the game starts.")
            st.write("게임이 시작하면 새로운 캐릭터를 임의로 정해드릴게요!")
            # persona = st.text_area('Persona', '')
            user_info = {
                "username": username
            }
            st.button("🔗 접속", key='button1', on_click=button1, kwargs={'HOST': HOST, 'PORT': PORT, 'user_info': user_info}, disabled=st.session_state.page!=0)

    def turn_page(self):

        with self.placeholder:
            # with st.spinner("⌛ Please wait until the server starts the turn."):
            with st.spinner("서버에서 입찰 세션을 시작하기까지 기다리는 중...\n\n아래에 이전 인터페이스가 떠도 버튼을 다시 누르지 말아주세요.\n\n안내와 다른 화면이 보일 경우 절대 새로고침(F5)를 누르지 마시고, 안내자에게 문의해 주세요."):
                if not st.session_state.session_control:
                    data = get_msg_from_server('start_bid')

                    data_list = data.split('\n\n')
                    st.session_state.session_control = True
                    st.session_state.button_disabled = False
                    st.session_state.server_socket.send('get_player'.encode())
                    data = get_msg_from_server('get_player')
                    st.session_state.player_data = data.split('\n\n')[1:]

                    if st.session_state.turn > 1:
                        st.session_state.server_socket.send('get_msg'.encode())
                        reply_data = get_msg_from_server('get_msg')
                        st.session_state.client_log[st.session_state.turn] += "\n\nday Received \n\n"
                        all_replys = 'Replys'.join(reply_data.split('Replys:')[1:])
                        st.session_state.client_log[st.session_state.turn] += all_replys
                        for reply in all_replys.split('\n\n'):
                            if ':' in reply:
                                name, msg = reply.split(':')
                                st.session_state.message_logdict[name.strip()] += f"{st.session_state.turn-1}:(received)**&#x{2459 + st.session_state.turn}; | :orange[답장▶️]** | {msg}\n\n"
        
        fc = self.placeholder.container()
        # start turn
        data_list = st.session_state.player_data
        if data_list[-3] not in [str(i) for i in range(8)]:
            turn = data_list[-2]
            st.session_state.round_num = turn
        else:
            turn = data_list[-3]
            st.session_state.round_num = turn

        bp, _, cp, _, rp = self.placeholder.columns([4.1,0.1,2.4,0.1,4.1])
        with cp.container():
            # st.markdown(f"### Turn {st.session_state.turn} / {turn} Bidding.")
            st.markdown(f"### 라운드 {st.session_state.turn} 입찰 세션") #@@@@
            # st.markdown(f"👤 **You are {st.session_state.name}.**")
            # on = st.toggle(f"Click to see Round Rule.")
            on = st.toggle(f"클릭하여 라운드 규칙을 확인해보세요!")
            if on:
                # st.markdown(f"  -   You need to pay {data_list[2]} fare.")
                # st.markdown(f"  -   Project will be success if all contribution is over {data_list[3]}.")
                # st.markdown(f"  -   If project success, you will receive an amount distributed according to the number of people, twice the total.")
                # st.markdown(f"  -   If project fail, you get nothing.")
                # st.markdown(f"  -   For example, if all people bid at least {int(data_list[2]) // 2}, you can deserve all {data_list[2]} fare.")
                # st.markdown(f"   -  Contribute smart to survive {turn} rounds!")
                st.markdown(f"  -   매 라운드마다 {data_list[2]}원이 참가비로 자동 차감됩니다.")
                st.markdown(f"  -   팀과 상관없이 전원 입찰 금액의 합이 {data_list[3]}원을 넘으면 목표 금액 달성 성공!")
                st.markdown(f"  -   목표 금액을 달성한 경우, 입찰 금액 합을 두 배로 하여 현재 게임 참가자 수만큼 나누어 배분합니다.")
                st.markdown(f"  -   목표 금액을 달성하지 못하는 경우, 투자했던 입찰 금액을 잃게 됩니다.")
                st.markdown(f"  -   예를 들어, 모든 플레이어가 적어도 {data_list[2]}를 입찰하는 경우, {int(data_list[2]) * 2} 만큼을 돌려 받기에 {data_list[2]}원의 참가비를 낼 수 있게 됩니다.")
                st.markdown(f"  -   물론 한 명이라도 이보다 적게 낸다면 균형은 깨지고, 생존이 어려워질 것입니다.")
                st.markdown(f"  -   튜토리얼에서 보셨듯이, 처음부터 상대팀을 탈락시킨다면 여러분은 마지막 라운드까지의 참가비를 낼 수 없어 아무도 승리하지 못할 것입니다.")
                st.markdown(f"  -   총 {turn} 라운드를 생존해야 하니 신중하게 입찰해주세요!")

            st.markdown(f"👤 **당신의 캐릭터는 {st.session_state.name}입니다.**")
            if st.session_state.turn != 1:
                ## graph
                # write_graph(st.session_state.turn)

                ## public messages
                write_public_messages(st.session_state.turn-1)

            ## first turn show team info
            else:
                # st.markdown(f"#### **Your status**")
                st.markdown(f"#### **나의 캐릭터**")
                col1, col2 = st.columns(2)
                col1.image(f'person_images/{st.session_state.name}.png')
                # col2.write(f"**Name**       : {data_list[0]}")
                col2.write(f"**이름**       : {data_list[0]}")
                #col2.write(f"**Endowment**  : {data_list[1]}")

                other_players_info = data_list[4].split('   ')[:-1]
                team_player_num = len(other_players_info)//2
                if 'tmp_chat_new_msg' not in st.session_state:
                    st.session_state.tmp_chat_new_msg = defaultdict(str)
                if st.session_state.name[0] < 'E':
                    # st.markdown(f"### :blue[Blue Team] (YOURS)")
                    st.markdown(f"### :blue[Blue Team] (나의 팀)")
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
                    # st.markdown(f"### :red[Red Team] (YOURS)")
                    st.markdown(f"### :red[Red Team] (나의 팀)")
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
            disabled = [True for i in range(len(st.session_state.player_names))]
            write_team_chat_container(bp, 'blue', st.session_state.player_names, disabled, "turn")
            write_team_chat_container(rp, 'red', st.session_state.player_names, disabled, "turn")

            
            st.markdown(f"#### 입찰액 목표 금액 (8명 합): **{data_list[3]}**")
            # st.markdown(f"### **Contribution for Turn {st.session_state.turn}**")
            st.markdown(f"### **라운드 {st.session_state.turn}의 입찰 금액**")
            with st.form(key='bid', border=False):
                # cur_bid = st.number_input("💰 Contribution", min_value=0, max_value=int(data_list[1]), key='bid')
                cur_bid = st.number_input("💰 입찰 금액", min_value=0, max_value=int(data_list[1]), key='bid')
                # submitted = st.form_submit_button("Submit")
                submitted = st.form_submit_button("금액 확인")
            # st.button("🛠️ Bet", key='button2', on_click=self.button2, kwargs={"cur_bid":cur_bid}, disabled=not submitted)
            st.button("🛠️ 입찰하기", key='button2', on_click=self.button2, kwargs={"cur_bid":cur_bid}, disabled=not submitted)



    def turn_waiting_page(self):
        with self.placeholder:
            # with st.spinner("⌛ Waiting for other players to finish betting..."):
            with st.spinner("⌛ 다른 플레이어들이 입찰을 마무리하기까지 기다리는 중...\n\n아래에 이전 인터페이스가 떠도 버튼을 다시 누르지 말아주세요.\n\n안내와 다른 화면이 보일 경우 절대 새로고침(F5)를 누르지 마시고, 안내자에게 문의해 주세요."):
                if not st.session_state.session_control:
                    data = get_msg_from_server('end_turn')
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
        print(names)
        write_team_chat_container(bp, 'blue', names, disabled, "turnend")
        write_team_chat_container(rp, 'red', names, disabled, "turnend")
        with cp:

            if not st.session_state.table_updated:
                total_conts = 0


            col1, col2, col3 = st.columns([1,2,1])
            # st.markdown(f"### Turn {st.session_state.turn} Ended.")
            st.markdown(f"### 라운드 {st.session_state.turn} 종료.")
            st.markdown(f"### :red[🏦 {data_list[1]}]")
            
            # st.markdown("#### **Contribution**")
            
            # col1, col2 = st.columns(2)
            
            
            other_players_info = data_list[2].split('\n')
            other_players_cont = data_list[3].split('\n')
            print(other_players_info)
            team_player_names = [pinfo.split(':')[0].strip() for pinfo in other_players_info]
            team_player_num = len(team_player_names)
            rctr = -1
            for i, pname in enumerate(team_player_names):
                if pname[0] > 'D':
                    rctr = i
                    break
            if rctr == -1:
                st.write(":blue[Blue Team]")
                bcols = st.columns(team_player_num)
            elif rctr == 0:
                st.write(":red[Red Team]")
                rcols = st.columns(team_player_num)
            else:
                st.write(":blue[Blue Team]")
                bcols = st.columns(rctr)
                st.write(":red[Red Team]")
                rcols = st.columns(team_player_num-rctr)
            blue_ctr = 0
            red_ctr = 0
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
                
                if c_name[0] < 'E':
                    col = bcols[blue_ctr]
                    blue_ctr+=1
                else:
                    col = rcols[red_ctr]
                    red_ctr+=1
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
                st.session_state.tmp_conts = total_conts
            st.session_state.table_updated = True
            # st.markdown("#### **Total Endowment change**")
            st.markdown("#### **총 입찰 금액**")
            st.markdown(f"입찰: {st.session_state.tmp_conts} / 목표: 1800")
            st.markdown("#### **나의 자금 변화**")
            if st.session_state.endowment_table[st.session_state.name][-1] >= st.session_state.endowment_table[st.session_state.name][-2]:
                st.write("➕ 💰")
                st.write(f"{st.session_state.endowment_table[st.session_state.name][-2]} ▶️ {st.session_state.endowment_table[st.session_state.name][-1]} (➕ {st.session_state.endowment_table[st.session_state.name][-1] - st.session_state.endowment_table[st.session_state.name][-2]})")

            else:
                st.write("➖ 💰")
                st.write(f"{st.session_state.endowment_table[st.session_state.name][-2]} ▶️ {st.session_state.endowment_table[st.session_state.name][-1]} (➖ {st.session_state.endowment_table[st.session_state.name][-2] - st.session_state.endowment_table[st.session_state.name][-1]})")

            
            
            ## graph
            #write_graph(st.session_state.turn+1)

            ## public messages
            if st.session_state.turn > 1:
                write_public_messages(st.session_state.turn-1)

            tmp_keys = list(st.session_state.endowment_table.keys()).copy()
            for k in tmp_keys:
                if k in st.session_state.endowment_table.keys():
                    if k != st.session_state.name:
                        if st.session_state.endowment_table[k][-1] <= 0:
                            st.session_state.contribution_table.pop(k, None)
                            st.session_state.endowment_table.pop(k, None)
            onclick = self.button3
            if data_list[4] != 'none':
                st.write('\n\n'.join(data_list[4].split('\n')))

                if cur_ed <= 0:
                    # st.write("❌ You have been eliminated.")
                    st.write("❌ 당신은 게임에서 탈락했습니다.")
                    onclick = endpage
                    public_message = ""
            
            if int(st.session_state.turn) == int(st.session_state.round_num):
                st.write("모든 라운드가 종료되었습니다.")
                st.write(data_list[5])
                onclick = endpage
                st.session_state.server_socket.send('received'.encode())
                public_message = ""

            if onclick != endpage:
                # st.write("### Write Public Message")
                st.write("### 전체 메시지를 작성해주세요")
                # on = st.toggle(f"Click to see Message Rule.")
                on = st.toggle(f"클릭하여 메시지 규칙을 확인해보세요!")
                if on:
                    # st.write("  -   You can write message as Korean, but please avoid using abbreviations or slang if possible. ")
                    # st.write("  -   Your message will be translated, proofread and delivered in English to opponents.")
                    # st.write("  -   Also, please do not use double enter in your message.")
                    st.write("  -   가능한 한 줄임말이나 비속어를 사용하지 않고 메시지를 작성해주세요. ")
                    st.write("  -   당신의 메시지는 영어로 번역되어 상대에게 전달됩니다.")
                    st.write("  -   메시지 작성시에는 더블 Enter는 지양해주세요.")
                with st.form(key='pmsg', border=False):
                    public_message = st.text_area(label="📧 전체 메시지", key='publics')
                    # submitted = st.form_submit_button("Submit")
                    submitted = st.form_submit_button("메시지 작성 완료")
                # st.button("➡️ End Turn", key='button3', on_click=onclick, kwargs={"checkbox": st.session_state.checkboxs, "public_message": public_message}, disabled=not submitted)
                st.button("➡️ 다음 라운드로 넘어가기", key='button3', on_click=onclick, kwargs={"checkbox": st.session_state.checkboxs, "public_message": public_message}, disabled=not submitted)
            else:
                # st.button("➡️ End Turn", key='button3', on_click=onclick)
                st.button("➡️ 게임 종료", key='button3', on_click=onclick)



    def turn_end_page(self):
        with self.placeholder:
            # with st.spinner("⌛ Waiting for other players to finish checking results..."):
            with st.spinner("⌛ 다른 플레이어들이 결과를 확인하기까지 기다리는 중......\n\n아래에 이전 인터페이스가 떠도 버튼을 다시 누르지 말아주세요.\n\n안내와 다른 화면이 보일 경우 절대 새로고침(F5)를 누르지 마시고, 안내자에게 문의해 주세요."):
                if not st.session_state.session_control:
                    data = get_msg_from_server(['start_turn', 'end_game'])
                    print(data)
                    data_list = data.split('\n\n')
                    if 'end_game' in data_list[0]:
                        st.session_state.server_socket.send('received'.encode())
                        st.session_state.session_control = True
                        onclick = self.button4(nextpage)
                    elif 'start_turn' in data_list[0]:
                        st.session_state.server_socket.send('received'.encode())
                        st.session_state.turn += 1
                        st.session_state.session_control = True
                        onclick = self.button4(msgpage)

        with self.placeholder.container():
            # st.write("🌒 Goto Next Turn Night...")
            st.write("이제부터 1대1로 개인 메시지를 작성해주세요")
            # st.button("➡️ Next", key='button4', on_click=onclick)
            st.button("➡️ 개인 메시지 세션으로 넘어가기", key='button4', on_click=onclick)

    def night_msg_page(self):
        with self.placeholder:
            # with st.spinner("🌒 Waiting for the server to start night..."):
            with st.spinner("서버에서 개인 메시지 세션을 시작하기까지 기다리는 중...\n\n아래에 이전 인터페이스가 떠도 버튼을 다시 누르지 말아주세요.\n\n안내와 다른 화면이 보일 경우 절대 새로고침(F5)를 누르지 마시고, 안내자에게 문의해 주세요."):
                if not st.session_state.session_control:
                    data = get_msg_from_server('STP')
                    public_messages = data.split('STP')[-1].split('\n\n')
                    st.session_state.public_messages = public_messages
                    st.session_state.server_socket.send('received'.encode())
                    st.session_state.session_control = True
                    st.session_state.server_socket.send('get_player_name'.encode())
                    data = get_msg_from_server('player_name')
                    pname_list = data.split('player_name')[-1].split('\n')
                    pname_list = [item.replace("start", "") for item in pname_list if item != 'start']
                    st.session_state.pname_list = pname_list


        bp, _, cp, _, rp = self.placeholder.columns([4.1,0.1,2.4,0.1,4.1])
        ## Chat interface : TODO dynamic with n, not just 4
        # Blue team
        names = st.session_state.player_names
        disabled = [False if name in list(st.session_state.contribution_table.keys()) else True for name in names]

        write_team_chat_container(bp, 'blue', names, disabled, 'night')
        write_team_chat_container(rp, 'red', names, disabled, "night")

        with cp.container():

            # st.markdown(f"### 🌒 **Turn {st.session_state.turn} Night Mailbox**")
            st.markdown(f"### **개인 메시지 세션**")

            ## graph
            # write_graph(st.session_state.turn)

            ## public messages
            write_public_messages(st.session_state.turn)

                    
            # st.write("### Write secret message")
            st.write("### 개인 메시지를 작성해주세요")
            # on = st.toggle(f"Click to see Message Rule.")
            on = st.toggle(f"클릭하여 메시지 규칙을 확인해보세요!")
            if on:
                # st.write("  -   You can write message as Korean, but please avoid using abbreviations or slang if possible.")
                # st.write("  -   Your message will be translated, proofread and delivered in English to opponents.")
                # st.write("  -   Also, please do not use double enter in your message.")
                st.write("  -   가능한 한 줄임말이나 비속어를 사용하지 않고 메시지를 작성해주세요. ")
                st.write("  -   당신의 메시지는 영어로 번역되어 상대에게 전달됩니다.")
                st.write("  -   메시지 작성시에는 더블 Enter는 지양해주세요.")
            
            # st.write("**If you have completed writing the message, click the checkbox and then click the Send button.**")
            st.write("**메시지 작성을 완료한 경우, 체크박스를 클릭한 후, 전송 버튼을 눌러주세요.**")
        
            # checked = st.checkbox('Done!', key = f'ch')
            checked = st.checkbox('메시지 작성 완료!', key = f'ch')
            # st.button('📤 Send', on_click=sending_mail, kwargs={'time':'night','player_msgs': st.session_state.tmp_chat_new_msg}, disabled = not checked)
            st.button('📤 메시지 전송', on_click=sending_mail, kwargs={'time':'night','player_msgs': st.session_state.tmp_chat_new_msg}, disabled = not checked)

    
    def day_msg_page(self):
        
        with self.placeholder:
            # with st.spinner("🌞 Waiting for the server to start day..."):
            with st.spinner("서버에서 답장 세션을 시작하기까지 기다리는 중...\n\n아래에 이전 인터페이스가 떠도 버튼을 다시 누르지 말아주세요.\n\n안내와 다른 화면이 보일 경우 절대 새로고침(F5)를 누르지 마시고, 안내자에게 문의해 주세요."):
                if not st.session_state.session_control:
                    data = get_msg_from_server('RPYS')
                    data_list = data.split('RPYS')[-1].split('\n\n')
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
                            st.session_state.message_logdict[name.strip()] += f"{st.session_state.turn}:(received)**&#x{2459 + st.session_state.turn}; | :green[제안▶️]** | {msg}\n\n"
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
        write_team_chat_container(bp, 'blue', names, disabled, 'day')
        write_team_chat_container(rp, 'red', names, disabled, 'day')

        with cp.container():
            
            # st.markdown(f"### 🌞 **Turn {st.session_state.turn} Day Mailbox**")
            st.markdown(f"### **라운드 {st.session_state.turn} 답장 세션**")

            ## graph
            # write_graph(st.session_state.turn)

            ## public messages
            write_public_messages(st.session_state.turn)

            # st.write("### Write replys")
            st.write("### 개인 메시지에 답장을 보내주세요!")
            if st.session_state.rdatas[0] != "":
                # st.write("📩 You've got messages from:")
                st.write("📩 다음 플레이어에게서 개인 메시지를 받았습니다:")
                cols = st.columns(len(st.session_state.rnames))
                for i, col in enumerate(cols):
                    cname = st.session_state.rnames[i]
                    if '(bot)' in cname:
                        cname = cname.split(' (bot)')[0]
                    col.write(st.session_state.rnames[i])
                    col.image(f'person_images/{cname}.png', width=100)
                # on = st.toggle(f"Click to see Message Rule.")
                on = st.toggle(f"클릭하여 메시지 규칙을 확인해보세요!")
                if on:
                    # st.write("  -   You can write message as Korean, but please avoid using abbreviations or slang if possible.")
                    # st.write("  -   Your message will be translated, proofread and delivered in English to opponents.")
                    # st.write("  -   Also, please do not use double enter in your message.")
                    st.write("  -   가능한 한 줄임말이나 비속어를 사용하지 않고 메시지를 작성해주세요. ")
                    st.write("  -   당신의 메시지는 영어로 번역되어 상대에게 전달됩니다.")
                    st.write("  -   메시지 작성시에는 더블 Enter는 지양해주세요.")
            else:
                # st.write("❌ You've got no messages.")
                st.write("❌ 받은 메시지가 없습니다.")
                # st.write("Just press Send button.")
                st.write("이 경우에도 메시지 전송 버튼을 눌러주세요.")

            
            # st.write("**If you have completed writing the message, click the checkbox and then click the Send button.**")
            st.write("**메시지 작성을 완료한 경우, 체크박스를 클릭한 후, 전송 버튼을 눌러주세요.**")
            
            # checked2 = st.checkbox('Done!', key = f'ch2')
            checked2 = st.checkbox('메시지 작성 완료!', key = f'ch2')
            # st.button('📤 Send', key='daysend', on_click=sending_mail, kwargs={'time': 'day','player_msgs': st.session_state.tmp_chat_new_msg}, disabled = not checked2)
            st.button('📤 메시지 전송', key='daysend', on_click=sending_mail, kwargs={'time': 'day','player_msgs': st.session_state.tmp_chat_new_msg}, disabled = not checked2)


    def game_end_page(self):
        # st.write("🎯 The game ends.")
        st.write("🎯 게임이 종료되었습니다.")
        # st.write("Thank you for participate!")
        st.write("참여해주셔서 감사합니다!")
        
        st.session_state.server_socket.send('received'.encode())
        # st.button("End the game", key='button6', on_click=initpage)
        st.button("게임 종료", key='button6', on_click=initpage)

    def blank_page(self):
        st.write("Some error find.")
        data = get_msg_from_server('page_fault')
        returns = data.split('\n\n')[1]
        st.session_state.page = int(returns)
