from .default_client import DefaultClient
from .water_allocation_client import WaterAllocationClient
from .public_goods_client import PublicGoodsClient

client_list = {
    "default": DefaultClient, 
    "WaterAllocation": WaterAllocationClient,
    "PublicGoods": PublicGoodsClient
    }

def select_client(name):
    return client_list[name]