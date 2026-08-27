import os
import sys
import disnake
from disnake.ext import commands


class DeveloperCog(commands.Cog):
    """Модуль управления ботом для разработчика и общая информация."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="about",
        description="Информация о боте и разработчике"
    )
    async def about(self, inter: disnake.ApplicationCommandInteraction):
        """Выводит краткую сводку о проекте."""
        info_text = (
            f"🤖 **Информация о боте**\n"
            f"──────────────────────────────\n"
            f"👨‍💻 **Разработчик:** <@980162487250980895>\n"
            f"⚙️ **Библиотека:** disnake (Python)\n"
            f"📡 **Задержка:** {round(self.bot.latency * 1000)}ms\n"
            f"──────────────────────────────"
        )
        await inter.response.send_message(embed=disnake.Embed(description=info_text, color=disnake.Color.blue()))


    async def cog_autocomplete(
        self, inter: disnake.ApplicationCommandInteraction, user_input: str
    ):
        cogs = [ext.replace("cogs.", "") for ext in self.bot.extensions.keys()]

        filtered_cogs = [
            cog for cog in cogs if user_input.lower() in cog.lower()
        ]

        return filtered_cogs[:25]

    @commands.slash_command(
        name="reload", description="[DEV] Перезагрузить конкретный cog"
    )
    @commands.has_permissions(administrator=True)
    async def reload_cog(
        self,
        inter: disnake.ApplicationCommandInteraction,
        cog_name: str = commands.Param(autocomplete=cog_autocomplete),
    ):
        try:
            formatted_name = (
                cog_name if cog_name.startswith("cogs.") else f"cogs.{cog_name}"
            )

            self.bot.reload_extension(formatted_name)
            await inter.response.send_message(
                f"✅ Модуль `{formatted_name}` успешно перезагружен!",
                ephemeral=True,
            )
        except Exception as e:
            await inter.response.send_message(
                f"❌ Ошибка при перезагрузке `{cog_name}`:\n```{e}```",
                ephemeral=True,
            )

    @commands.slash_command(
        name="restart",
        description="[DEV] Полная перезагрузка бота"
    )
    @commands.has_permissions(administrator=True)
    async def restart_bot(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message("🔄 Перезапуск бота...", ephemeral=True)
        os.execv(sys.executable, [sys.executable] + sys.argv)


    @reload_cog.error
    @restart_bot.error
    async def owner_error_handler(inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.NotOwner):
            await inter.response.send_message(
                "⛔ У вас нет прав для использования этой команды.", 
                ephemeral=True
            )


def setup(bot: commands.Bot):
    bot.add_cog(DeveloperCog(bot))