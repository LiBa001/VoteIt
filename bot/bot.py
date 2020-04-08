from discord.ext import commands
import logging
from .context import Context
import asyncio
import aiohttp
import os


logger = logging.getLogger(__name__)


class Bot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super(Bot, self).__init__(*args, **kwargs)

        self.dbl_session = aiohttp.ClientSession(loop=self.loop, headers={'Authorization': os.getenv('DBL_API_TOKEN')})
        self.loop.create_task(self._update_stats())

    async def _update_stats(self):
        """This function runs every 30 minutes to automatically update the server count."""

        await self.wait_until_ready()

        dbl_api_url = f'https://discordbots.org/api/bots/{self.user.id}/stats'
        stats = {'shard_count': self.shard_count}

        while not self.is_closed():
            logger.info('attempting to post server count')
            server_count = len(self.guilds)

            for shard_id in self.shard_ids:
                shard_server_count = server_count // len(self.shard_ids)

                if shard_id == self.shard_ids[-1]:
                    shard_server_count += server_count % len(self.shard_ids)

                stats['shard_id'] = shard_id
                stats['server_count'] = shard_server_count

                async with self.dbl_session.post(dbl_api_url, json=stats) as resp:
                    logger.info(f'posted server count for shard {shard_id} ({shard_server_count}; code: {resp.status})')

            await asyncio.sleep(1800)

        await self.dbl_session.close()

    async def on_message(self, message):
        ctx = await self.get_context(message, cls=Context)
        await self.invoke(ctx)
