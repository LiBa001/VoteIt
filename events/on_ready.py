import logging


logger = logging.getLogger(__name__)


async def on_ready():
    logger.info("======== logged in ========")
