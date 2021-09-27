from bs4 import BeautifulSoup
import requests
import json
_r_items = requests.get("https://api.warframe.market/v1/items")
_t_items = _r_items.text
item_data = json.loads(_t_items)["payload"]["items"]


def wfm_load():
    """
    Returns (item_data, item_names)
    """
    item_names = []
    [item_names.append(item["item_name"]) for item in item_data]
    return item_data, item_names


def wfm_find(item_name, item_data):
    """
    Finds in list and returns item data\n
    Based on wfm_load dictionaries
    """
    for item in item_data:
        if item["item_name"] == item_name:
            return item
    return None


def wfm_search(item):
    """
    Takes item as argument\n
    Returns (price_avg, count)
    """
    _url = item["url_name"]
    _r = requests.get(f"https://api.warframe.market/v1/items/{_url}/orders")
    orders = json.loads(_r.text)["payload"]["orders"]
    count = len(orders)
    price_avg = 0
    _wa_e1 = _wa_e2 = 0
    _cheapest = {"price": 1000, "user": None}
    for order in orders:
        if order["order_type"] == "sell" and (order["platinum"] < 1000 and order["quantity"]) and order["user"]["status"] != "offline":
            if order["platinum"] < _cheapest["price"] and order["user"]["status"] == "ingame":
                _cheapest["price"] = order["platinum"]
                _cheapest["user"] = order["user"]["ingame_name"]
            _wa_e1 += order["platinum"] * order["quantity"]
            _wa_e2 += order["quantity"]
    price_avg = round(_wa_e1 / _wa_e2, 2)
    return price_avg, count, _cheapest


def wfm_formatorders(orders: dict):
    """
    Formats user orders to readable text\n
    `user: {thumb, item_name, id, order_id, url_name,
    platinum, quantity, last_update}`
    """
    _o = []
    for order in orders:
        _item = {}
        _item["thumb"] = order["item"]["thumb"]
        _item["item_name"] = order["item"]["en"]["item_name"]
        _item["id"] = order["item"]["id"]
        _item["order_id"] = order["id"]
        _item["url_name"] = order["item"]["url_name"]
        _item["platinum"] = order["platinum"]
        _item["quantity"] = order["quantity"]
        _item["last_update"] = order["last_update"]
        _o.append(_item)
    return _o


def wfm_getuser(username):
    """
    Scrapes warframe.market user profile
    for data and returns (orders_sell, orders_buy)
    """
    _req = requests.get(
        f"https://warframe.market/profile/{username}").text
    soup = BeautifulSoup(_req, "html.parser")
    _user_orders = soup.find(id="application-state")
    try:
        _user_orders = _user_orders.contents[0]
    except AttributeError:
        return None, None
    orders_sell = json.loads(_user_orders)["payload"]["sell_orders"]
    orders_buy = json.loads(_user_orders)["payload"]["buy_orders"]
    return orders_sell, orders_buy


def wfm_getuserf(username):
    """
    Formats wfm_getuser using wfm_formatuser
    """
    _sub_sell, _sub_buy = wfm_getuser(username)
    if _sub_sell or _sub_buy is None:
        return
    orders_sell = wfm_formatorders(_sub_sell)
    orders_buy = wfm_formatorders(_sub_buy)
    return orders_sell, orders_buy

# TODO: Fix wfm_getuserf not returning anything
# TODO: Total listings & plot value in wfm [user]
