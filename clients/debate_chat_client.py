from .default_client import *
import streamlit as st
import pandas as pd
import logging
import time
import os 
from glob import glob
from PIL import Image
from streamlit_extras.bottom_container import bottom
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

debate_dict = {
    "3D_printing": "./game_texts/debate_reading_3D_printing.txt",
    "basic_income": "./game_texts/debate_reading_basic_income.txt",
    "Car-hailing_services": "./game_texts/debate_reading_car_sharing.txt",
    "Artificial_womb_technology": "./game_texts/debate_reading_art_womb.txt"
}


def initpage():
    st.session_state.page = 0

def prevpage():
    st.session_state.page -= 1

def readpage():
    st.session_state.page = 4

def chatpage():
    st.session_state.page = 2



def get_msg_from_server(splitter):
    data = ""
    buf = b""
    while "END" not in data or splitter not in data:
        buf += st.session_state.server_socket.recv(1024)
        try:
            data = buf.decode("utf-8")
        except:
            continue
        if splitter in data:
            data = data.split(splitter)[1]
            if "END" in data:
                data = splitter + data.split("END")[0]
                break
            else:
                buf = (splitter + data).encode()
                continue
    return data



### button functions
def button1_thread(HOST, PORT, user_info):
    PORT = int(PORT)
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((HOST, PORT))
    except:
        st.warning("connection refused. try again.")
        return
    sending_data = "\n\n".join([str(user_info[k]) for k in user_info.keys()])
    sending_data = "ready\n\n" + sending_data
    server_socket.send(sending_data.encode())
    st.session_state.server_socket = server_socket
    data = server_socket.recv(1024).decode("utf-8")
    print(data)
    if data.split("\n\n")[0] == "accepted":
        name = data.split("\n\n")[1]
        st.session_state.name = name
        st.session_state.idle_toggle = False
        st.session_state.page += 1
    else:
        st.warning("player name duplicated.")

def button_end():
    st.session_state.client_chats = [k for k in st.session_state.client_chats if k !='']
    client_chat_log = "\n\n".join(
        [
            f"{st.session_state.timestamps[i]} {n}: {msg}"
            for i, (n, msg) in enumerate(st.session_state.client_chats)
        ]
    )
    st.session_state.server_socket.send(
        f"end_game\n\n{st.session_state.real_name}\n\n{client_chat_log}END".encode()
    )
    st.session_state.client_chats = []
    st.session_state.timestamps = []
    st.session_state.msg_history = []
    st.session_state.restarted = True

def button_restart():
    prevpage()

def do_idle_toggle():
    st.session_state.server_socket.send("idle".encode())
    st.session_state.waiting_idle = True

def do_activate_toggle(n):
    st.session_state.server_socket.send(f'activate\n\n{n.lower()}'.encode())

def is_player_name(new_name):
    new_name = new_name.lower()
    for player_name in st.session_state.player_names:
        if (
            new_name == player_name
            or new_name in player_name
            or new_name == st.session_state.name.lower()
        ):
            return True
    return False


class DebateChatClient(DefaultClient):
    def __init__(self, placeholder):
        super().__init__(placeholder)
        if "timestamps" not in st.session_state:
            st.session_state.timestamps = []

    def parsing_history(self, msgs):
        return [
            (msg.split(":")[0], ":".join(msg.split(":")[1:])) if ":" in msg else ""
            for msg in msgs.split("\n\n")
        ]

    ### page implementations
    def main_page(self, HOST, PORT):
        with self.placeholder.container():
            #st.markdown("### 🎮 Welcome to the New Chatting!")
            st.markdown("### 🎮 새로운 채팅에 오신 것을 환영합니다!")

            #st.write("Type your information and connect to your server!")
            st.write("정보를 입력하시면 서버에 연결해드리겠습니다!")
            HOST = st.text_input("🌐 IP Address", value="127.0.0.1")
            PORT = st.text_input("🌐 IP Port", value="20912")
            username = st.text_input("📛 Your Name", "")
            #st.write("You will receive a new nickname when the game starts.")
            st.write("게임이 시작하면 새로운 캐릭터를 임의로 정해드릴게요!")
            # persona = st.text_area('Persona', '')
            user_info = {"username": username}
            st.button(
                "🔗 접속",
                key="button1",
                on_click=button1_thread,
                kwargs={
                    "HOST": HOST,
                    "PORT": PORT,
                    "user_info": user_info,
                },
                disabled=st.session_state.page != 0,
            )

    def turn_page(self):
        if not st.session_state.session_control:
            # with st.spinner("⌛ Please wait until the server starts new session."):
            with st.spinner("⌛ 서버에서 세션을 시작할 때까지 잠시 기다려주세요. 아래에 이전 인터페이스가 떠도 버튼을 다시 누르거나 새로고침을 하지 말아주세요."):
                data = get_msg_from_server("start")
                data_list = data.split("\n\n")
                st.session_state.ai_jobs = data_list[1].split("@")
                st.session_state.ai_persona_summary = data_list[2].split("@")
                debate_name = data_list[3]
                st.session_state.player_names = data_list[4].split(', ')
                st.session_state.player_names = [n.lower() for n in st.session_state.player_names]
                st.session_state.activate_toggle = {k: False for k in st.session_state.player_names}
                st.session_state.waiting_idle = 0
                st.session_state.debate_path = debate_dict[debate_name]
                st.session_state.first_rendering = True
                st.session_state.session_control = True
                st.session_state.ai_acting = True
                st.session_state.restarted = False
        with self.placeholder.container():
            #st.markdown("## 📖 First, read basic debate theme instuctions below.")
            st.markdown("## 📖 먼저, 이번 채팅의 주제에 관한 기본 설명을 읽어주세요.")
            #st.markdown("### 👍 After read all, press next button to go to chat page.")
            st.markdown("### 👍 모두 읽었다면, 아래 버튼을 눌러 채팅 페이지로 넘어가세요.")
            with open(st.session_state.debate_path, "r",encoding='utf-8') as f:
                text = f.read()
            with st.container(height=600):
                st.markdown(text)
            st.button("➡️ 채팅", key="button2", on_click=nextpage)

    # chat_page
    def turn_waiting_page(self):
       
        if st.session_state.first_rendering:
            self.placeholder.write(" ")
            st.session_state.first_rendering = False 
        cc = self.placeholder.container()
        # with self.placeholder:
        with st.sidebar:
            st.button("세션 끝내기", disabled=st.session_state.ai_acting, on_click=button_end)
            st.button("문서 다시보기", disabled=st.session_state.ai_acting, on_click=readpage)

            if len(st.session_state.ai_persona_summary) > 1:
                for i in range(len(st.session_state.ai_persona_summary)):
                    st.title(f"**{st.session_state.player_names[i].capitalize()}**")
                    st.markdown(f"{st.session_state.ai_persona_summary[i]}")
                    try:
                        # Load and resize the image
                        avatar_paths = glob(f"person_images/{st.session_state.player_names[i].capitalize()}.png")
                        if len(avatar_paths) > 0:
                            image = Image.open(avatar_paths[0])
                        else:
                            image = Image.open("person_images/default.png")
                        fixed_size_image = image.resize((200, 200))  # Resize to 200x200 pixels
                        st.image(
                            fixed_size_image
                        )
                    except:
                        image = Image.open("person_images/default.png")
                        fixed_size_image = image.resize((200, 200))  # Resize to 200x200 pixels
                        st.image(
                            fixed_size_image
                        )
                    st.divider()

            else:
                st.markdown(f"**Bot_A**")
                st.markdown(f"**Job**: {st.session_state.ai_jobs[0]}")
                st.markdown(f"**Persona**: {st.session_state.ai_persona_summary[0]}")

            # end game
            # st.button("Clear chatting", on_click=button_clear)

            # st.image(f'person_images/kakao_default.jpeg')
        # print("reruned")

        # check chat history
        # st.session_state.client_thread.get_msg = True
        # while True:
        #     if not st.session_state.client_thread.get_msg:
        #         break
        with cc:
            for i, chats in enumerate(st.session_state.client_chats):
                if chats == "":
                    continue

                name, chat = chats
                if is_player_name(name):
                    if name.capitalize() == st.session_state.name:
                        # with st.chat_message("user", avatar=f'person_images/{name.capitalize()}.png'):
                        with st.chat_message("user"):
                            st.markdown(chat.replace('\n', '\n\n'))
                    else:
                        avatar_paths = glob(f"person_images/{name.capitalize()}.png")
                        if len(avatar_paths) > 0:
                            avatar_path = avatar_paths[0]
                        else:
                            avatar_path = "person_images/default.png"
                        with st.chat_message(
                            "ai", avatar=avatar_path
                        ):
                            chat = chat.replace('\n', '\n\n')
                            st.markdown(f"**[ {name} ]**: {chat}")

        # new input
        if len(st.session_state.ai_jobs) > 1:
            with bottom():
                # input_message = st.chat_input()
                # with st.expander("Activate/Deactivate Bots (You must activate at least one to chat.)"):
                #     len_rows = len(st.session_state.player_names) // 4 + 1
                #     i=0
                #     for row in range(len_rows):
                #         cols = st.columns(4)
                #         for col in cols:
                #             if i >= len(st.session_state.player_names):
                #                 break
                #             player_name = st.session_state.player_names[i]
                #             st.session_state.activate_toggle[player_name] = col.toggle(f"{player_name.capitalize()}", on_change=do_activate_toggle, kwargs={"n":player_name})
                #             i+=1
                            
                # ic1.button(
                #     "발언권 넘기기",
                #     on_click=do_idle_toggle,
                #     disabled=(
                #         st.session_state.ai_acting
                #     ),
                # )
                imsg_str = (
                    "여기에 메시지를 작성해주세요."
                    if not st.session_state.ai_acting
                    else "상대방이 메시지를 작성 중입니다. 잠시 기다려 주세요."
                )
                input_message = st.chat_input(
                    imsg_str, disabled=(st.session_state.ai_acting)
                )
        else:
            input_message = st.chat_input()
        if input_message:
            with cc.chat_message("user"):
                st.markdown(input_message)
                if len(st.session_state.client_chats) == 0:
                    st.session_state.client_chats.append(
                        (st.session_state.name, input_message)
                    )
                    st.session_state.timestamps.append(
                        datetime.now().strftime("(%H:%M:%S) ")
                    )
            st.session_state.server_socket.send(f"send\n\n{input_message}".encode())
            st.session_state.waiting_idle = True
            time.sleep(0.2)
            # st.session_state.client_thread.new_input_msg = input_message
            # st.session_state.client_thread.send_msg = True
        # time.sleep(0.5)
        waiting_timeout = 30
        start_waiting_time = time.time()
        while True:
            if time.time() - start_waiting_time > waiting_timeout:
                st.session_state.waiting_idle = False
                st.rerun()
            local_waiting_idle = False
            st.session_state.server_socket.send("get".encode())
            try:
                tmp_ai_acting = st.session_state.ai_acting
                new_data = get_msg_from_server("START").split("START")[1]
                st.session_state.ai_acting = True if new_data.split('\n\n')[0] == "True" else False
                new_msg = '\n\n'.join(new_data.split('\n\n')[1:])
                if new_msg == "":
                    print("None")
                elif new_msg == "NOHISTORY":
                    print("skipped")
                elif new_msg == "NOUPDATE":
                    print("no update")
                else:
                    print("new msg")
                    print(new_msg)
                    st.session_state.msg_history = (
                        new_msg  # st.session_state.client_thread.new_msg
                    )
                    parsed_chats = self.parsing_history(st.session_state.msg_history)
                    if len(parsed_chats) > len(st.session_state.client_chats):
                        for i in range(
                            len(parsed_chats) - len(st.session_state.client_chats)
                        ):
                            st.session_state.timestamps.append(
                                datetime.now().strftime("(%H:%M:%S) ")
                            )
                        for i, chats in enumerate(
                            parsed_chats[len(st.session_state.client_chats) :]
                        ):
                            t_len = len(st.session_state.client_chats) + i
                            if chats == "":
                                continue
                            name, chat = chats
                            if is_player_name(name):
                                if name.capitalize() == st.session_state.name:
                                    pass
                                else:
                                    avatar_paths = glob(f"person_images/{name.capitalize()}.png")
                                    if len(avatar_paths) > 0:
                                        avatar_path = avatar_paths[0]
                                    else:
                                        avatar_path = "person_images/default.png"
                                    with cc.chat_message(
                                        "ai",
                                        avatar=avatar_path,
                                    ):
                                        chat.replace('\n', '\n\n')
                                        st.markdown(f"**[ {name} ]**: {chat}")
                                    local_waiting_idle = True

                        st.session_state.client_chats = parsed_chats
                        if st.session_state.waiting_idle and local_waiting_idle:
                            st.session_state.waiting_idle = False
                            st.rerun()
                    # st.rerun()
                if tmp_ai_acting != st.session_state.ai_acting:
                    st.rerun()
            except Exception as e:
                print(e)
            time.sleep(0.5)

    # end page
    def turn_end_page(self):
        # st.write("Session end. Goto New Session...")
        if st.session_state.restarted:
            # with st.spinner("⌛ Please wait until the server starts new session."):
            with st.spinner("⌛ 서버에서 세션을 시작할 때까지 잠시 기다려주세요. 아래에 이전 인터페이스가 떠도 버튼을 다시 누르거나 새로고침을 하지 말아주세요."):
                data = get_msg_from_server("start")
                data_list = data.split("\n\n")
                st.session_state.ai_jobs = data_list[1].split("@")
                st.session_state.ai_persona_summary = data_list[2].split("@")
                debate_name = data_list[3]
                st.session_state.player_names = data_list[4].split(', ')
                st.session_state.player_names = [n.lower() for n in st.session_state.player_names]
                st.session_state.activate_toggle = {k: False for k in st.session_state.player_names}
                st.session_state.waiting_idle = 0
                st.session_state.debate_path = debate_dict[debate_name]
                st.session_state.first_rendering = True
                st.session_state.session_control = True
                st.session_state.ai_acting = True
                st.session_state.restarted = False
        with self.placeholder.container():
            with open(st.session_state.debate_path, "r",encoding='utf-8') as f:
                text = f.read()
            with st.container(height=600):
                st.markdown(text)
            st.button("다음 세션", on_click=button_restart)

    # sub page
    def game_end_page(self):
        with self.placeholder.container():
            with open(st.session_state.debate_path, "r",encoding='utf-8') as f:
                text = f.read()
            with st.container(height=600):
                st.markdown(text)
            st.button("➡️ 돌아가기", key="buttonback", on_click=chatpage)
