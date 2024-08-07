import streamlit as st
import argparse
from collections import defaultdict
from clients import client_list, select_client


st.set_page_config(layout='wide')

# HOST / PORT setting
# socket info - for remote server
# HOST = '0.0.0.0'
# PORT = 20912 
# socket info - for local
HOST = '127.0.0.1'
PORT = 20912

placeholder = st.empty()
# initiating session_state variables
def initiation():
    if "page" not in st.session_state:
        st.session_state.page = 0
    if "game_name" not in st.session_state:
        st.session_state.game_name = "Default"
    if "name" not in st.session_state:
        st.session_state.name = ""
    if "client_id" not in st.session_state:
        st.session_state.client_id = ""
    if "server_socket" not in st.session_state:
        st.session_state.server_socket = 0
    if "turn" not in st.session_state:
        st.session_state.turn = 1
    if "iswin" not in st.session_state:
        st.session_state.iswin = False
    if "nowsup" not in st.session_state:
        st.session_state.nowsup = 0
    if "session_control" not in st.session_state:
        st.session_state.session_control = False
    if "client_log" not in st.session_state:
        st.session_state.client_log = defaultdict(str)
    if "rnames" not in st.session_state:
        st.session_state.rnames = []
    if "rdatas" not in st.session_state:
        st.session_state.rdatas = []
    if "player_data" not in st.session_state:
        st.session_state.player_data = []
    if "pname_list" not in st.session_state:
        st.session_state.pname_list = []
    if "contribution_table" not in st.session_state:
        st.session_state.contribution_table = {}
    if "endowment_table" not in st.session_state:
        st.session_state.endowment_table = {}
    if "msg_history" not in st.session_state:
        st.session_state.msg_history = ""
    if "client_chats" not in st.session_state:
        st.session_state.client_chats = []
    if "message_logdict" not in st.session_state:
        st.session_state.message_logdict = defaultdict(str)
    if "status_logdict" not in st.session_state:
        st.session_state.status_logdict = {}
    if "checkboxs" not in st.session_state:
        st.session_state.checkboxs = []
    if "public_messages" not in st.session_state:
        st.session_state.public_messages = []
    if "table_updated" not in st.session_state:
        st.session_state.table_updated = False
    if "tmp_submitted" not in st.session_state:
        st.session_state.tmp_submitted = {}
    if "tmp_conts" not in st.session_state:
        st.session_state.tmp_conts = 0
    if "player_names" not in st.session_state:
        st.session_state.player_names = []
    if "round_num" not in st.session_state:
        st.session_state.round_num = 0


if __name__ == '__main__':
    initiation()
    curClient = select_client(st.session_state.game_name)
    dc = curClient(placeholder)
    if st.session_state.page == 0:
        dc.main_page(HOST, PORT)
    elif st.session_state.page == 1:
        dc.turn_page()
    elif st.session_state.page == 2:
        dc.turn_waiting_page()
    elif st.session_state.page == 3:
        dc.turn_end_page()
    elif st.session_state.page == 4:
        dc.game_end_page()
    elif st.session_state.page == 5:
        dc.night_msg_page()
    elif st.session_state.page == 6:
        dc.day_msg_page()
    else:
        dc.blank_page()
