import hmac
import time
import json
import base64
import errors
import base64
import hashlib

from models import request
from typing import Union, Literal
from dataclasses import dataclass

@dataclass
class ChallangeData:
    rblx_challange_id: str
    rblx_challange_metadata: str
    rblx_challange_type: Union[Literal["twostepverification"], str]

class AutoPass:
    def __init__(self, secret: str):
        self.secret = secret
        
    @staticmethod
    def totp(secret: str) -> Union[str, errors.InvalidOtp]:
        try:
            # boy this took me long time googling 
            interval = 30
            digits = 6
            digest = hashlib.sha1
            
            missing_padding = len(secret) % 8
            if missing_padding:
                secret += '=' * (8 - missing_padding)

            key = base64.b32decode(secret, casefold = True)
            counter = int(time.time() // interval)
            counter_bytes = counter.to_bytes(8, byteorder="big")
            hmac_hash = hmac.new(key, counter_bytes, digest).digest()
            
            offset = hmac_hash[-1] & 0x0F
            code = (
                (hmac_hash[offset] & 0x7F) << 24 |
                (hmac_hash[offset + 1] & 0xFF) << 16 |
                (hmac_hash[offset + 2] & 0xFF) << 8 |
                (hmac_hash[offset + 3] & 0xFF)
            )
            
            return str(code % (10 ** digits)).zfill(digits)
        except:
            raise errors.InvalidOtp()
        
    async def __call__(self, previous_request: "request.Request", challenge_data: ChallangeData) -> Union["request.Request", errors.InvalidOtp]:
        if challenge_data.rblx_challange_type != "twostepverification":
            raise errors.InvalidChallangeType("Change your security settings to use authenticator only")
        
        meta_data: dict
        meta_data = json.loads(base64.b64decode(challenge_data.rblx_challange_metadata).decode("utf-8"))
        
        response = request.Request(
            url = f"https://twostepverification.roblox.com/v1/users/{previous_request.user_id}/challenges/authenticator/verify",
            method = "post",
            headers = previous_request.headers,
            
            proxy = previous_request.proxy,
            session = previous_request.session,
            close_session = previous_request.close_session,
            json_data = {
                "challengeId": meta_data.get("challengeId"),
                "actionType": meta_data.get("actionType"),
                "code": self.totp(self.secret)
            }
        )
        try:
            response = await response.send()
        except:
            raise errors.InvalidOtp()
        
        try:
            dumped_challange_meta_data = str(json.dumps({
                "verificationToken": response.response_json.verificationToken,
                "rememberDevice": False,
                "challengeId": meta_data.get("challengeId"),
                "actionType": meta_data.get("actionType")
            }))
            response = await request.Request(
                url = "https://apis.roblox.com/challenge/v1/continue",
                method = "post",
                headers = previous_request.headers,
                
                proxy = previous_request.proxy,
                session = previous_request.session,
                close_session = previous_request.close_session,
                
                json_data = {
                    "challengeId": challenge_data.rblx_challange_id,
                    "challengeMetadata": dumped_challange_meta_data,
                    "challengeType": challenge_data.rblx_challange_type
                }
            ).send()
        except:
            raise errors.InvalidOtp()
        
        if not previous_request.headers.raw_headers:
           previous_request.headers.raw_headers = {}
            
        previous_request.headers.raw_headers["x-csrf-token"] = previous_request.headers.x_csrf_token
        previous_request.headers.raw_headers["rblx-challenge-id"] = challenge_data.rblx_challange_id
        previous_request.headers.raw_headers["rblx-challenge-metadata"] = base64.b64encode(dumped_challange_meta_data.replace(" ", "").encode('utf-8')).decode('utf-8')
        previous_request.headers.raw_headers["rblx-challenge-type"] = challenge_data.rblx_challange_type
        
        return previous_request