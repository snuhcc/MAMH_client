from .default_client import DefaultClient
from .water_allocation_client import WaterAllocationClient
from .public_goods_client import PublicGoodsClient
from .movie_chat_client import MovieChatClient
from .debate_chat_client import DebateChatClient
from .public_goods_client_ui import PublicGoodsClientUI
from .todo_chat_client import TodoChatClient

client_list = {
    "Default": DefaultClient, 
    "WaterAllocation": WaterAllocationClient,
    "PublicGoods": PublicGoodsClient,
    "PublicGoodsUI" : PublicGoodsClientUI,
    "MovieChat": MovieChatClient,
    "DebateChat": DebateChatClient,
    "TodoChat" : TodoChatClient,
    }

def select_client(name):
    return client_list[name]