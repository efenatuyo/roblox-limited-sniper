import re
import time
import time
import json
import errors
import random
import asyncio
import aiohttp

from models import request, items
from typing import Optional, Union, List, Dict, TYPE_CHECKING

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.layout import Layout
from rich.box import HEAVY

if TYPE_CHECKING:
    from sniper import WatchLimiteds

class UIManager:
    def __init__(self, total_proxies: int):
        self.start_time = time.time()
        self.total_proxies = total_proxies
        self.total_requests = 0
        self.total_items_checked = 0
        self.total_items_bought = 0
        self.lock = asyncio.Lock()
        self.logs = []

    async def log_event(self, message: str):
        async with self.lock:
            timestamp = time.strftime('%H:%M:%S')
            self.logs.append(f"[{timestamp}] {message}")
            if len(self.logs) > 20:
                self.logs.pop(0)

    async def add_requests(self, count: int):
        async with self.lock:
            self.total_requests += count

    async def add_items(self, count: int):
        async with self.lock:
            self.total_items_checked += count

    async def add_items_bought(self, count: int = 1):
        async with self.lock:
            self.total_items_bought += count

    def render(self):
        elapsed = int(time.time() - self.start_time)
        mins, secs = divmod(elapsed, 60)
        uptime = f"{mins}m {secs}s"

        stats = Table.grid(padding=1)
        stats.add_column(justify="right", style="bold cyan")
        stats.add_column(style="bold white")

        stats.add_row("Proxies", str(self.total_proxies))
        stats.add_row("Total Requests", str(self.total_requests))
        stats.add_row("Items Checked", str(self.total_items_checked))
        stats.add_row("Items Bought", str(self.total_items_bought))
        stats.add_row("Uptime", uptime)

        log_panel = Panel(
            "\n".join(self.logs) if self.logs else "[grey]No logs yet...",
            title="Recent Events",
            border_style="yellow",
            padding=(1, 2)
        )

        layout = Layout()
        layout.split(
            Layout(Panel(stats, title="Global Stats", border_style="green", padding=(1, 2)), name="upper", size=14),
            Layout(log_panel, name="lower")
        )

        return layout

async def run_ui(ui_manager: UIManager):
    console = Console()
    with Live(ui_manager.render(), refresh_per_second=2, console=console) as live:
        while True:
            await asyncio.sleep(0.5)
            live.update(ui_manager.render())
                
class CombinedAttribute:
    def __init__(self, watch_limiteds: 'WatchLimiteds'):
        self.watch_limiteds = watch_limiteds
        
    def __getattr__(self, name):
        return getattr(self.watch_limiteds, name)

    def __setattr__(self, name, value):
        if name == "watch_limiteds" or name.startswith("_"):
            super().__setattr__(name, value)
        else:
            setattr(self.watch_limiteds, name, value)

    def __delattr__(self, name):
        if name == "watch_limiteds" or name.startswith("_"):
            super().__delattr__(name)
        else:
            delattr(self.watch_limiteds, name)

class Iterator:
    def __init__(self, data: List[items.Generic]):
        self.original_data = data[:]
        self._reset_pool()

    def _reset_pool(self, ):
        self.pool = self.original_data[:]
        random.shuffle(self.pool)
        self.index = 0

    def __call__(self, batch_size: int) -> List[items.Generic]:
        if batch_size >= len(self.original_data):
            return self.original_data[:]
        
        batch = []
        
        while len(batch) < batch_size:
            if self.index >= len(self.pool):
                self._reset_pool()

            needed = batch_size - len(batch)
            available = len(self.pool) - self.index
            take = min(needed, available)

            batch.extend(self.pool[self.index:self.index + take])
            self.index += take

        return batch

class XCsrfTokenWaiter:
    def __init__(self, cookie: Optional[str] = None, proxy: Optional[str] = None, on_start: bool = False):
        self.last_call_time = time.time()
        
        self.cookie = cookie
        self.proxy = proxy
        
        self.x_crsf_token = None if not on_start else asyncio.run(self.generate_x_csrf_token(self.cookie, self.proxy))
    
    async def __call__(self) -> Union[None, str]:
        now = time.time()
        elapsed = now - self.last_call_time
        
        if elapsed > 120:
            self.x_crsf_token = await self.generate_x_csrf_token(self.cookie, self.proxy)
            if self.x_crsf_token:
                self.last_call_time = now
                
        return self.x_crsf_token
    
    @staticmethod
    async def generate_x_csrf_token(cookie: Union[str, None], proxy: Union[str, None]) -> Union[str, None]:
        response: request.Response
        response = await request.Request(
            url = "https://auth.roblox.com/v2/logout",
            method = "post",
            headers = request.Headers(
                cookies = {".ROBLOSECURITY": cookie}
            ),
            success_status_codes = [403],
            proxy = proxy
        ).send()
        return response.response_headers.x_csrf_token

class RolimonsDataScraper:
    def __init__(self):
        self.last_call_time = time.time()
        self.item_data: Dict[str, items.RolimonsData] = None
        
    async def __call__(self) -> Union[None, Dict[str, items.RolimonsData]]:
        now = time.time()
        elapsed = now - self.last_call_time
        
        if elapsed > 600 or not self.item_data:
            self.item_data = await self.retrieve_item_data()
            if self.item_data:
                self.last_call_time = now
                
        return self.item_data
    
    @staticmethod
    def extract_variable(html: str) -> Union[None, Dict[str, List]]:
        item_pattern = re.compile(r'var\s+item_details\s*=\s*(\{.*?\});', re.DOTALL)

        match = item_pattern.search(html)
        if match:
            js_data = match.group(1)
            
            try:
                parsed_data = json.loads(js_data)
                return parsed_data
            except json.JSONDecodeError as e:
                return None
        else:
            return None
    
    @staticmethod
    async def retrieve_item_data() -> Dict[str, items.RolimonsData]:
        headers = request.Headers( raw_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        })
        
        response: request.Response
        response = await request.Request(
            url = "https://www.rolimons.com/catalog",
            method = "get",
            headers = headers
        ).send()
        
        item_details = RolimonsDataScraper.extract_variable(response.response_text)
        if item_details:
            items_dataclass = {}
            for item_id, data in item_details.items():
                items_dataclass[item_id] = items.RolimonsData(
                    rap = data[8],
                    value = data[16]
                )
            
            return items_dataclass
        else:
            return None

class UnlockCookie:
    def __init__(self, cookie: str) -> None:
        self.cookie = cookie

    async def __call__(self) -> Union[str, 'errors.InvalidCookie']:
        try:
            async with aiohttp.ClientSession() as session:
                csrf_token = await XCsrfTokenWaiter.generate_x_csrf_token(self.cookie, None)
                auth_ticket = await self.get_authentication_ticket(session, csrf_token)
                new_cookie = await self.redeem_authentication_ticket(session, csrf_token, auth_ticket)

                if new_cookie:
                    return new_cookie
                else:
                    raise Exception("No .ROBLOSECURITY cookie returned")

        except Exception as reason:
            raise errors.InvalidCookie(reason)

    async def get_authentication_ticket(self, session: aiohttp.ClientSession, x_csrf_token: str) -> str:
        req = request.Request(
            url="https://auth.roblox.com/v1/authentication-ticket",
            method="post",
            headers=request.Headers(
                x_csrf_token=x_csrf_token,
                cookies={".ROBLOSECURITY": self.cookie},
                raw_headers={
                    "rbxauthenticationnegotiation": "1",
                    "referer": "https://www.roblox.com/camel",
                    "Content-Type": "application/json",
                    "x-csrf-token": x_csrf_token,
                },
            ),
            session=session,
            close_session=False,
        )

        res = await req.send()

        ticket = res.response_headers.raw_headers.get("rbx-authentication-ticket")
        if not ticket:
            raise ValueError("Failed to retrieve authentication ticket")
        return ticket

    async def redeem_authentication_ticket(self, session: aiohttp.ClientSession, x_csrf_token: str, authentication_ticket: str) -> str:
        req = request.Request(
            url="https://auth.roblox.com/v1/authentication-ticket/redeem",
            method="post",
            headers=request.Headers(
                x_csrf_token=x_csrf_token,
                raw_headers={
                    "rbxauthenticationnegotiation": "1",
                    "x-csrf-token": x_csrf_token,
                },
            ),
            json_data={"authenticationTicket": authentication_ticket},
            session=session,
            close_session=False,
        )

        res = await req.send()

        roblosecurity = res.response_headers.cookies.get(".ROBLOSECURITY")
        if not roblosecurity:
            raise ValueError("Failed to retrieve .ROBLOSECURITY from response")
        return roblosecurity
