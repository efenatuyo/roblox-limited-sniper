from models import items, config, request
from typing import Union, Tuple, Optional, List, Dict

import errors
import helpers
import asyncio

class BuyLimited:
    def __init__(self, user_data: config.Account, buy_data: items.BuyData) -> None:
        self.user_data = user_data
        self.buy_data = buy_data

     
    async def __call__(self) -> Union[bool, Tuple[bool, request.ResponseJsons.BuyResponse]]:
        try:
            url = f"https://apis.roblox.com/marketplace-sales/v1/item/{self.buy_data.collectible_item_id}/purchase-resale"
            response: request.Response
            response = await request.Request(
                url = url,
                method = "post",
                headers = request.Headers(
                    x_csrf_token = await self.user_data.x_csrf_token(),
                    cookies = {".ROBLOSECURITY": self.user_data.cookie}
                ),
                json_data = request.RequestJsons.jsonify_api_broad(url, self.buy_data),
                otp_token = self.user_data.otp_token,
                close_session = False,
                user_id = self.user_data.user_id
            ).send()
            
            if response.response_json.purchased:
                return True, response.response_json
            else:
                return False, response.response_json
            
        except errors.Request.Failed:
            return False

class WatchLimiteds:
    def __init__(self, config: config.Settings, rolimon_limiteds: helpers.RolimonsDataScraper) -> None:
        self.webhook = config.webhook
        
        self.account = config.account
        
        self.generic_settings = config.buy_settings.generic_settings
        self.custom_settings = config.buy_settings.custom_settings
        self.limiteds = config.limiteds
        self.rolimon_limiteds = rolimon_limiteds
        self.proxies = config.proxies
        self.ui_manager = helpers.UIManager(total_proxies = len(config.proxies))
        self.requests = 0

    async def __call__(self):
        threads = [
            ProxyThread(self, proxy).watch() # self is the own obj for shared vars
            for proxy in self.proxies
        ]
        
        await asyncio.gather(*threads, helpers.run_ui(ui_manager = self.ui_manager))
        
class ProxyThread(helpers.CombinedAttribute):
    webhook: str
    account: config.Account
    generic_settings: config.ItemSettings
    custom_settings: Union[None, Dict[str, config.ItemSettings]]
    limiteds: helpers.Iterator
    rolimon_limiteds: helpers.RolimonsDataScraper
    ui_manager: helpers.UIManager
    requests: int 
    
    def __init__(self, watch_limiteds: WatchLimiteds, proxy: str):
        super().__init__(watch_limiteds)
        
        self._proxy = proxy
    
    def check_if_item_elligable(self, item_data: items.Data, item_value_rap: items.RolimonsData) -> bool:
        # checking if custom config is avaible. Using custom config if avaible else generic
        item_buy_config: config.ItemSettings
        item_buy_config = self.generic_settings if not str(item_data.item_id) in self.custom_settings else self.custom_settings[str(item_data.item_id)]
        if item_buy_config.price_measurer == "value":
            if item_value_rap.value:
                base_value_item = item_value_rap.value
            else:
                return False
        elif item_buy_config.price_measurer == "rap":
            base_value_item = item_value_rap.rap
        elif item_buy_config.price_measurer == "value_rap":
            # use value if avaible else rap
            base_value_item = item_value_rap.value if item_value_rap.value else item_value_rap.rap
            
        if item_buy_config.min_percentage_off and not (base_value_item * (item_buy_config.min_percentage_off / 100)) > item_data.lowest_resale_price:
            return False
        if item_buy_config.min_robux_off and not base_value_item - item_data.lowest_resale_price > item_buy_config.min_robux_off:
            return False
        if item_buy_config.max_robux_cost and not item_data.lowest_resale_price >= item_buy_config.max_robux_cost:
            return False
        
        return True
    
    @staticmethod
    async def get_resale_data(item: items.Data) -> Union[request.ResponseJsons.ResaleResponse, errors.Request.Failed]:
        response = await request.Request(
            url = f"https://apis.roblox.com/marketplace-sales/v1/item/{item.collectible_item_id}/resellers?limit=1",
            method = "get",
            retries = 5
        ).send()
        return response.response_json
        
    async def handle_response(self, item_list: request.ResponseJsons.ItemDetails):
        rolimons_limited = self.rolimon_limiteds
        for item in item_list.items:
            if str(item.item_id) in await rolimons_limited():
                if self.check_if_item_elligable(item, (await rolimons_limited())[str(item.item_id)]):
                    resale_data: request.ResponseJsons.ResaleResponse
                    resale_data = await self.get_resale_data(item)
                    item.lowest_resale_price = resale_data.price
                    if self.check_if_item_elligable(item, (await rolimons_limited())[str(item.item_id)]): # check again just incase price has changed
                        buy_data = items.BuyData(
                            collectible_item_id = item.collectible_item_id,
                            collectible_item_instance_id = resale_data.collectible_item_instance_id,
                            collectible_product_id = resale_data.collectible_product_id,
                            expected_price = resale_data.price,
                            expected_purchaser_id = str(self.account.user_id)
                        )
                        
                        buy_response = await BuyLimited(self.account, buy_data)()
                        
                        webhook = request.RequestJsons.WebhookMessage(
                            content = f"{'✅' if buy_response and buy_response[0] else '❌'} Bought Item {item.item_id} for {buy_data.expected_price} R$ | ProductID: {buy_data.collectible_product_id} | InstanceID: {buy_data.collectible_item_instance_id} | Buyer: {buy_data.expected_purchaser_id}"
                        )
                        await self.ui_manager.log_event(webhook.content)
                        await self.ui_manager.add_items_bought()
                        
                        await request.Request(
                            url = self.webhook,
                            method = "post",
                            json_data = request.RequestJsons.jsonify_api_broad(self.webhook, webhook),
                            success_status_codes = [204]
                        ).send()
                        
    async def get_batch_item_data(self, url: str, items: List[items.Generic], proxy = str) -> Union[None, errors.Request.Failed]:
        response = await request.Request(
            url = url,
            method = "post",
            
            headers = request.Headers(
                cookies = {".ROBLOSECURITY": self.account.cookie},
                x_csrf_token = await self.account.x_csrf_token()
            ),
            json_data = request.RequestJsons.jsonify_api_broad(url, items),
            proxy = proxy
        ).send()
        await self.ui_manager.add_requests(1)
        await self.ui_manager.add_items(len(items))
        await self.handle_response(response.response_json)

    async def watch(self):
        while True:
            try:
                await asyncio.gather(*[
                    self.get_batch_item_data(url = "https://catalog.roblox.com/v1/catalog/items/details", items = self.limiteds(120), proxy = self._proxy),
                    self.get_batch_item_data(url = "https://apis.roblox.com/marketplace-items/v1/items/details", items = self.limiteds(30), proxy = self._proxy)
                ])
            except:
                continue
            finally:
                await asyncio.sleep(1)
    
    
             
# ben mutlu alo efe
# alo
# knk sus köy bok ya