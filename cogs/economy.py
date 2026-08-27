import disnake
from disnake.ext import commands

from functions.utils import create_embed


class EconomyCog(commands.Cog):
    """Модуль экономической системы бота."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot








def setup(bot: commands.Bot):
    bot.add_cog(EconomyCog(bot))