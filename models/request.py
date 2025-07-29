import re
import errors
import aiohttp
import authenticator

from dataclasses import dataclass, field, fields, is_dataclass
from typing import List, Optional, Union, Callable, Awaitable
from models import items

class ResponseJsons:
    
    @dataclass
    class ItemDetails:
        items: List[items.Data]
    
    @dataclass
    class CookieInfo:
        user_id: int
        user_name: str
        display_name: str
    
    @dataclass
    class BuyResponse:
        purchased_result: str
        purchased: bool
        pending: bool
        error_message: Union[str, None]
    
    @dataclass
    class ResaleResponse:
        collectible_item_instance_id: str
        collectible_product_id: str
        seller_id: int
        price: int

    @dataclass
    class TwoStepVerification:
        verificationToken: str
        
    @staticmethod
    def validate_json(url, response_json: dict) -> Union[None, "ResponseJsons.ItemDetails", "ResponseJsons.CookieInfo", "ResponseJsons.ResaleResponse", "ResponseJsons.TwoStepVerification"]:
        if url == "https://catalog.roblox.com/v1/catalog/items/details":
            items_return = []
            
            for item in response_json.get("data", []):
                items_return.append(
                    items.Data(
                        item_id = item["id"],
                        product_id = item["productId"],
                        collectible_item_id = item["collectibleItemId"],
                        lowest_resale_price = item["lowestResalePrice"]
                    )
                )
            
            return ResponseJsons.ItemDetails(items = items_return)
        
        elif url == "https://apis.roblox.com/marketplace-items/v1/items/details":
            items_return = []
            
            for item in response_json:
                items_return.append(
                    items.Data(
                        item_id = item["itemTargetId"],
                        product_id = item["productTargetId"],
                        collectible_item_id = item["collectibleItemId"],
                        lowest_resale_price = item["lowestResalePrice"]
                    )
                )
            
            return ResponseJsons.ItemDetails(items = items_return)
        
        elif url == "https://users.roblox.com/v1/users/authenticated":
                        
            return ResponseJsons.CookieInfo(
                user_id = response_json["id"],
                user_name = response_json["name"],
                display_name = response_json["displayName"]
            )
        
        elif re.match(r"^https://apis.roblox.com/marketplace-sales/v1/item/.*/purchase-resale$", url):
            return ResponseJsons.BuyResponse(
                purchased_result = response_json["purchaseResult"],
                purchased = response_json["purchased"],
                pending = response_json["pending"],
                error_message = response_json["errorMessage"]
            )
            
        elif re.match(r"^https://apis.roblox.com/marketplace-sales/v1/item/.*/resellers\?limit=1$", url):
            
            return ResponseJsons.ResaleResponse(
                collectible_item_instance_id = response_json["data"][0]["collectibleItemInstanceId"],
                collectible_product_id = response_json["data"][0]["collectibleProductId"],
                seller_id = response_json["data"][0]["seller"]["sellerId"],
                price = response_json["data"][0]["price"]
            )
        
        elif url == "https://twostepverification.roblox.com/v1/users/3254298971/challenges/authenticator/verify":
            
            return ResponseJsons.TwoStepVerification(
                verificationToken = response_json["verificationToken"]
            )
            
class RequestJsons:
    
    @dataclass
    class WebhookMessage: # adding more fields later on
        content: str 
    
    def jsonify_api_broad(url: str, data: Union["RequestJsons.WebhookMessage", items.BuyData, List[items.Generic]]) -> dict:
        if url == "https://apis.roblox.com/marketplace-items/v1/items/details":
            return {"itemIds": [item.collectible_item_id for item in data]}
        elif url == "https://catalog.roblox.com/v1/catalog/items/details":
            return {"items": [{"id": item.item_id} for item in data]}
        elif re.match(r"^https://apis.roblox.com/marketplace-sales/v1/item/.*/purchase-resale$", url):
            return {
                "collectibleItemId": data.collectible_item_id,
                "collectibleItemInstanceId": data.collectible_item_instance_id, # from resale data pls
                "collectibleProductId": data.collectible_product_id,
                "expectedCurrency": data.expected_currency,
                "expectedPrice": data.expected_price,
                "expectedPurchaserId": data.expected_purchaser_id,
                "expectedPurchaserType": data.expected_purchaser_type,
                "expectedSeller": data.expected_seller_id,
                "expectedSellerType": data.expected_seller_type,
                "idempotencyKey": data.idempotency_key
            }
        
        elif re.match(r"^https:\/\/(?:canary\.|ptb\.)?discord(app)?\.com\/api\/webhooks\/\d+\/[\w-]+$", url):
            
            return {
                "content": data.content
            }
        
@dataclass
class Headers:
    x_csrf_token: Optional[str] = ""
    cookies: Optional[dict] = field(default_factory=lambda: {})
    raw_headers: Optional[dict] = None
    
@dataclass
class Response:
    status_code: int
    
    response_headers: Headers
    response_json: Union[None, ResponseJsons.ItemDetails, ResponseJsons.CookieInfo, ResponseJsons.BuyResponse]
    response_text: str

@dataclass
class Request:
    url: str
    method: str
    
    headers: Optional[Headers] = field(default_factory=lambda: Headers())
    json_data: Optional[dict] = None

    proxy: Optional[str] = None
    
    session: Optional[aiohttp.ClientSession] = None
    close_session: Optional[bool] = True

    success_status_codes: Optional[List[int]] = field(default_factory=lambda: [200])
    retries: Optional[int] = 1
    
    otp_token: Optional["authenticator.AutoPass"] = None
    user_id: Optional[int] = 0
    
    auth: bool = False
    
    async def send(self) -> Union[Response, errors.Request.Failed]:
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        exceptions = []
        
        for i in range(self.retries):
            try:
                method: Callable[..., Awaitable[aiohttp.ClientResponse]]
                method = getattr(self.session, self.method)
                headers = {"x-csrf-token": str(self.headers.x_csrf_token)} if not self.headers.raw_headers else self.headers.raw_headers
                response = await method(self.url, headers = headers, cookies = self.headers.cookies, json = self.json_data, proxy = self.proxy)
                if response.status in self.success_status_codes or (response.status == 403 and self.otp_token and self.user_id):
                    if response.status == 403 and self.otp_token and self.user_id and "Challenge" in await response.text():
                        challange_data = authenticator.ChallangeData(
                            rblx_challange_id = response.headers.get("rblx-challenge-id"),
                            rblx_challange_metadata = response.headers.get("rblx-challenge-metadata"),
                            rblx_challange_type = response.headers.get("rblx-challenge-type")
                        )
                        request_formatted = await self.otp_token(self, challenge_data = challange_data)
                        request_formatted.close_session = True
                        return await request_formatted.send()
                        
                    response_cookies = {cookie.key: cookie.value for cookie in self.session.cookie_jar}
                    response_headers = Headers(x_csrf_token = response.headers.get("x-csrf-token"), cookies = response_cookies, raw_headers = dict(response.headers))
                    
                    try:
                        response_json = ResponseJsons.validate_json(self.url, await response.json())
                    except:
                        response_json = None
                    if self.close_session:
                        await self.session.close()  
                    
                    return Response(status_code = response.status, response_headers = response_headers, response_json = response_json, response_text = await response.text())                    
                else:
                    print(await response.text())
                    raise errors.Request.InvalidStatus(response.status)
            except Exception as reason:
                exceptions.append(reason)
        
        if self.close_session:
            await self.session.close()
        
        raise errors.Request.Failed(exceptions)