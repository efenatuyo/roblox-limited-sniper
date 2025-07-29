import json
import errors
import helpers
import asyncio
import authenticator

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Union, Literal
from models import request, items

@dataclass
class Account:
    cookie: str
    otp_token: str
    
    x_csrf_token: helpers.XCsrfTokenWaiter

    user_id: str = field(init = None)
    user_name: str = field(init = None)
    
        
    def __post_init__(self) -> Union[None, errors.InvalidCookie]:
        try:
            headers = request.Headers(cookies = {".ROBLOSECURITY": self.cookie})
            
            response = asyncio.run(
                request.Request(
                    url = "https://users.roblox.com/v1/users/authenticated",
                    method = "get",
                    headers = headers
                ).send()
            )
            
            self.cookie = asyncio.run(helpers.UnlockCookie(self.cookie)())
            self.user_id = response.response_json.user_id
            self.user_name = response.response_json.user_name
            self.x_csrf_token = helpers.XCsrfTokenWaiter(cookie = self.cookie, on_start = True)
        except errors.Request.Failed as reason:
            raise errors.InvalidCookie(reason)

@dataclass
class ItemSettings:
    min_percentage_off: int
    min_robux_off: Optional[int] = None
    max_robux_cost: Optional[int] = None
    price_measurer: Optional[Literal["value", "rap", "value_rap"]] = "rap"

@dataclass
class BuySettings:
    generic_settings: ItemSettings
    custom_settings: Optional[Dict[str, ItemSettings]] = None

@dataclass
class Settings:
    webhook: Union[None, str]
    account: Account
    buy_settings: BuySettings
    limiteds: helpers.Iterator
    proxies: List[str]


def create_item_settings(data):
    return ItemSettings(
        min_percentage_off=data["min_percentage_off"],
        min_robux_off=data.get("min_robux_off"),
        max_robux_cost=data.get("max_robux_cost"),
        price_measurer=data.get("price_measurer")
    )

def __init__() -> Union[Settings, errors.Config.CantAccess, errors.Config.InvalidFormat, errors.Config.MissingValues]:
    try:
        config = open("config.json", "r")
        try:
            file_json = json.loads(config.read())
        except Exception as reason:
            raise errors.InvalidConfigFormat(reason)
    except Exception as reason:
        raise errors.CantAccessConfig(reason)
            
    try:
        account = Account(
            cookie = file_json["account"]["cookie"],
            otp_token = authenticator.AutoPass(file_json["account"]["otp_token"]),
            x_csrf_token = helpers.XCsrfTokenWaiter(cookie = file_json["account"]["cookie"], proxy = None, on_start = True)
        )
                
        buy_settings_data = file_json["buy_settings"]
        buy_settings_generic_data = buy_settings_data["generic_settings"]
        
        if buy_settings_generic_data.get("price_measurer") not in ("rap", "value", "value_rap", None):
            raise errors.Config.InvalidFormat(f"Accepted price_measurers (value, rap, value_rap, None). Received: {buy_settings_generic_data['price_measurer']}")
             
        generic_settings = create_item_settings(buy_settings_generic_data)
        
        buy_settings_custom_data = buy_settings_data.get("custom_settings")
        
        if buy_settings_custom_data:
            custom_settings = {}
            
            for item_id, data in buy_settings_custom_data.items():
                if data.get("price_measurer") not in ("rap", "value", "value_rap", None):
                    raise errors.Config.InvalidFormat(f"Accepted price_measurers (value, rap, value_rap, None). Received: {data['price_measurer']}")
             
                custom_item_settings = create_item_settings(data)
                
                custom_settings[item_id] = custom_item_settings
        
            
        buy_settings =  BuySettings(
            generic_settings = generic_settings,
            custom_settings = custom_settings
            
        )
        
        limiteds = file_json["limiteds"]
        if not limiteds:
            raise errors.Config.MissingValues("Limiteds list can not be empty")
        for limited in limiteds:
            if len(limited) != 2:
                raise errors.Config.MissingValues("Limited needs both item id and collectible item id")
        
        proxies = file_json["proxies"]
        if not proxies:
            raise errors.Config.MissingValues("Proxy list can not be empty")
        
        settings = Settings(
            webhook = file_json.get("webhook"),
            account = account,
            buy_settings = buy_settings,
            limiteds = helpers.Iterator(data = [items.Generic(item_id = limited[0], collectible_item_id = limited[1]) 
                                                for limited in limiteds]),
            proxies = proxies
        )
        
        return settings
    
    except KeyError as reason:
        raise errors.Config.MissingValues(reason)
    