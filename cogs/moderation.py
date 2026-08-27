import disnake
from disnake.ext import commands

from functions.utils import create_embed


class ModerationCog(commands.Cog):
    """Модуль модерации и управления сервером."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        print(f"Участник {member} присоединился к серверу {member.guild.name}.")

    @commands.slash_command(
        name="clear",
        description="Удалить указанное количество сообщений"
    )
    @commands.has_permissions(manage_messages=True)
    async def clear(
        self, 
        inter: disnake.ApplicationCommandInteraction, 
        amount: int
    ):
        await inter.response.defer(ephemeral=True)
        
        deleted = await inter.channel.purge(limit=amount)
        
        embed = create_embed(
            title="Очистка чата",
            description=f"Успешно удалено сообщений: {len(deleted)}",
            color=disnake.Color.orange()
        )
        
        await inter.edit_original_message(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(ModerationCog(bot))