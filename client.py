import streamlit as st
import argparse
from collections import defaultdict
from clients import client_list, select_client

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
    if "message_logdict" not in st.session_state:
        st.session_state.message_logdict = defaultdict(str)
    if "status_logdict" not in st.session_state:
        st.session_state.status_logdict = {}


if __name__ == '__main__':
    initiation()
    game_name = "PublicGoods"
    curClient = select_client(game_name)
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
