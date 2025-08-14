"""Discord bot entry: exports config and client class."""
from . import config
from .discord_bot import DiscordBot

__all__ = ["config", "DiscordBot"]
