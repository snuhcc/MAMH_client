from .default_client import DefaultClient
from .water_allocation_client import WaterAllocationClient
from .public_goods_client import PublicGoodsClient
from .movie_chat_client import MovieChatClient
from .debate_chat_client import DebateChatClient

client_list = {
    "Default": DefaultClient, 
    "WaterAllocation": WaterAllocationClient,
    "PublicGoods": PublicGoodsClient,
    "MovieChat": MovieChatClient,
    "DebateChat": DebateChatClient,
    }

def select_client(name):
    return client_list[name]