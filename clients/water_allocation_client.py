from .default_client import *
import streamlit as st

class WaterAllocationClient(DefaultClient):
    def __init__(self):
        super().__init__()
        pass

    @staticmethod
    def button2(**kwargs):
        cur_bid = kwargs['cur_bid']
        st.session_state.server_socket.send(f'bid\n\n{cur_bid}'.encode())
        st.session_state.session_control = False
        nextpage()

    ### page implementations
    @staticmethod
    def main_page(HOST, PORT):
        st.write("Welcome to new Game!")

        st.write("Type your information and connect to your server!")
        name = st.text_input('Nickname', 'Tester')
        requirement = st.number_input('Water Requirements', 0)
        daily_salary = st.number_input('daily_salary', 0)
        persona = st.text_area('Persona', f'You are {name} and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 20 days by acquiring the water resources. ')
        user_info = {
            "requirement": requirement,
            "daily_salary": daily_salary,
            "persona": persona
        }
        st.button("Connect", key='button1', on_click=button1, kwargs={'HOST': HOST, 'PORT': PORT, 'name': name, 'user_info': user_info}, disabled=st.session_state.page!=0)

    def turn_page(self):
        st.write("Please wait until server start turn.")
        if not st.session_state.session_control:
            while True:
                data = st.session_state.server_socket.recv(1024).decode('utf-8')
                print(data)
                if data == 'start':
                    st.session_state.session_control = True
                    break
                else:
                    print('error?')
        st.write(f"**Turn {st.session_state.turn} started.**")
        user_info = st.container(border=True)
        user_info.write(f"Your status")
        st.session_state.server_socket.send('get_player'.encode())
        data = st.session_state.server_socket.recv(1024).decode('utf-8')
        data_list = data.split('\n\n')
        print(data_list[0])
        n = data_list[0]
        user_info.write(f"")
        user_info.write(f"NAME: {data_list[0]}")
        user_info.write(f"REQUREMENT:{data_list[1]}\tBALANCE:{data_list[2]}\tHEALTH POINT:{data_list[3]}\tNO_DRINK:{data_list[4]}")
        user_info.write("")
        user_info.write(f"You will get {data_list[5]} supply when win this turn.")
        user_info.write("")
        user_info.write(f"Other players info:")
        for t in data_list[6].split('   '):
            user_info.write(t)

        st.session_state.nowsup = data_list[5]
        bc = st.container(border=True)
        cur_bid = bc.number_input('Current turn\'s bid', min_value=0, max_value=int(data_list[2]))
        st.button("Bet!", key='button2', on_click=self.button2,kwargs={'cur_bid': cur_bid}, disabled=st.session_state.page != 1)
    
    def turn_waiting_page(self):
        st.write("Waiting other players finish bet...")
        while True:
            data = st.session_state.server_socket.recv(1024).decode('utf-8')
            data_list = data.split('\n\n')
            if data_list[0] == 'end_turn':
                if data_list[1] == 'win':
                    st.session_state.iswin = True
                elif data_list[1] == 'lose':
                    st.session_state.iswin = False
                break
            else:
                print('error?')
        st.write(f"**Turn {st.session_state.turn} ended.**")
        if st.session_state.iswin:
            st.write(f"*You won this turn! get {st.session_state.nowsup} supply, get 2 life.*")
        else:
            st.write(f"You lost this turn. lost 1 life.")

        st.button("End turn", key='button3', on_click=self.button3)

    def turn_end_page(self):
        st.write("Waiting other players finish checking result...")
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

        st.button("Next", key='button4', on_click=onclick)


    def game_end_page(self):
        st.write("Not implemented.")
        # print result / save result / query....