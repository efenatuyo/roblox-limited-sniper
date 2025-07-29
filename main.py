from models import config

import sniper
import helpers
import asyncio

user_config = config.__init__()
rolimon_limiteds = helpers.RolimonsDataScraper()

asyncio.run(sniper.WatchLimiteds(user_config, rolimon_limiteds)())
