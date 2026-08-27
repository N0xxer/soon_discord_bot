import json
import disnake
from disnake import ui
from disnake.ext import commands

from functions.db_helpers import (
    clear_channel_owner,
    get_owner_by_channel_id,
    get_voice_config,
    update_voice_config,
)


class VoiceChannelsCog(commands.Cog):
    """Модуль голосовых каналов бота."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.create_channel_id = 1542594925068165361
        self.voice_category_id = 1454071917207228447  # ID категории для авто-комнат
        self.ignored_channel_ids = {
            self.create_channel_id, 1374039734971797515, 1454072091501662301, 1454072119221682247
        }

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState
    ):
        """Создание и удаление временных каналов."""
        # 1. Создание канала
        if after.channel and after.channel.id == self.create_channel_id:
            guild = member.guild
            category = after.channel.category

            saved_name = await get_voice_config(member.id, "name")
            saved_limit = await get_voice_config(member.id, "user_limit")
            is_private = await get_voice_config(member.id, "private")
            blocked_raw = await get_voice_config(member.id, "blocked_users")

            channel_name = saved_name if saved_name else f"🔹・{member.display_name[:20]}"
            user_limit = saved_limit if saved_limit is not None else 0

            overwrites = {
                member: disnake.PermissionOverwrite(connect=True, view_channel=True, move_members=True)
            }

            if is_private == 1:
                overwrites[guild.default_role] = disnake.PermissionOverwrite(connect=False)

            if blocked_raw:
                try:
                    blocked_ids = json.loads(blocked_raw)
                    for u_id in blocked_ids:
                        target = guild.get_member(u_id)
                        if target:
                            overwrites[target] = disnake.PermissionOverwrite(connect=False)
                except json.JSONDecodeError:
                    pass

            position = len(category.channels) if category else None

            new_channel = await guild.create_voice_channel(
                name=channel_name,
                category=category,
                position=position,
                user_limit=user_limit,
                overwrites=overwrites,
            )

            await update_voice_config(member.id, "vc_channels_ids", str(new_channel.id))
            await member.move_to(new_channel)

            timestamp = int(disnake.utils.utcnow().timestamp())

            components = [
                ui.Container(
                    ui.TextDisplay(
                        f"# Комната {channel_name}\n"
                        f"**Владелец:** {member.mention}\n"
                        f"**Создана:** <t:{timestamp}:f>"
                    ),
                    ui.Separator(),
                    ui.TextDisplay("## Управление комнатой"),
                    ui.Section(
                        "Изменить название комнаты",
                        accessory=ui.Button(emoji="✏️", custom_id="vc_rename", style=disnake.ButtonStyle.secondary),
                    ),
                    ui.Section(
                        "Лимит участников",
                        accessory=ui.Button(emoji="♾️", custom_id="vc_limit", style=disnake.ButtonStyle.secondary),
                    ),
                    ui.Section(
                        "Приватность",
                        accessory=ui.Button(emoji="🔒", custom_id="vc_privacy", style=disnake.ButtonStyle.secondary),
                    ),
                    ui.Section(
                        "Передать владельца",
                        accessory=ui.Button(emoji="👑", custom_id="vc_transfer", style=disnake.ButtonStyle.secondary),
                    ),
                    ui.Section(
                        "Пригласить",
                        accessory=ui.Button(emoji="➕", custom_id="vc_invite", style=disnake.ButtonStyle.secondary),
                    ),
                    ui.Section(
                        "Кикнуть",
                        accessory=ui.Button(emoji="✖️", custom_id="vc_kick", style=disnake.ButtonStyle.secondary),
                    ),
                    ui.Section(
                        "Заблокировать",
                        accessory=ui.Button(emoji="⚠️", custom_id="vc_ban", style=disnake.ButtonStyle.secondary),
                    ),
                )
            ]

            await new_channel.send(
                components=components,
                allowed_mentions=disnake.AllowedMentions.none(),
            )

        # 2. Удаление канала
        if before.channel and isinstance(before.channel, disnake.VoiceChannel):
            channel = before.channel
            is_target_category = channel.category_id == self.voice_category_id
            is_not_ignored = channel.id not in self.ignored_channel_ids

            if is_target_category and is_not_ignored:
                # Исключаем пользователя, который выходит/переходит, из списка оставшихся
                remaining_members = [m for m in channel.members if m.id != member.id]

                if len(remaining_members) == 0:
                    owner_id = await get_owner_by_channel_id(channel.id)
                    if owner_id:
                        await clear_channel_owner(channel.id)
                        try:
                            await channel.delete()
                        except disnake.NotFound:
                            pass

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        """Открытие модальных окон при клике на кнопки."""
        custom_id = inter.component.custom_id
        if not custom_id.startswith("vc_"):
            return

        channel = inter.channel
        if not isinstance(channel, disnake.VoiceChannel):
            return

        owner_id = await get_owner_by_channel_id(channel.id)
        if not owner_id or inter.author.id != owner_id:
            await inter.response.send_message("Вы не являетесь владельцем этой комнаты.", ephemeral=True)
            return

        # 1. Изменение названия комнаты
        if custom_id == "vc_rename":
            await inter.response.send_modal(
                title="Изменение названия",
                custom_id="modal_vc_rename",
                components=[
                    ui.Label(
                        "Название комнаты",
                        ui.TextInput(
                            placeholder="Введите новое название...",
                            custom_id="input_vc_name",
                            max_length=50,
                            required=True,
                        ),
                    )
                ],
            )

        # 2. Лимит участников
        elif custom_id == "vc_limit":
            await inter.response.send_modal(
                title="Лимит участников",
                custom_id="modal_vc_limit",
                components=[
                    ui.Label(
                        "Лимит мест (0 — без лимита)",
                        ui.TextInput(
                            placeholder="Число от 0 до 99",
                            custom_id="input_vc_limit",
                            max_length=2,
                            required=True,
                        ),
                    )
                ],
            )

        # 3. Приватность
        elif custom_id == "vc_privacy":
            current_private = await get_voice_config(inter.author.id, "private")
            new_private_state = 0 if current_private == 1 else 1

            default_role = inter.guild.default_role
            can_connect = None if new_private_state == 0 else False
            await channel.set_permissions(default_role, connect=can_connect)

            await update_voice_config(inter.author.id, "private", new_private_state)
            status_text = "закрыта для всех" if new_private_state == 1 else "открыта для всех"
            await inter.response.send_message(f"Комната теперь **{status_text}**.", ephemeral=True)

        # 4. Передача владельца (только среди участников в канале)
        elif custom_id == "vc_transfer":
            members_in_channel = [m for m in channel.members if m.id != inter.author.id and not m.bot]
            if not members_in_channel:
                await inter.response.send_message("В канале нет других участников для передачи прав.", ephemeral=True)
                return

            options = [
                disnake.SelectOption(label=m.display_name, value=str(m.id))
                for m in members_in_channel[:25]
            ]

            await inter.response.send_modal(
                title="Передать права владельца",
                custom_id="modal_vc_transfer",
                components=[
                    ui.Label(
                        "Новый владелец комнаты",
                        ui.StringSelect(
                            custom_id="select_vc_transfer",
                            placeholder="Выберите участника из канала...",
                            options=options,
                        ),
                    )
                ],
            )

        # 5. Пригласить (выбор среди всех пользователей сервера)
        elif custom_id == "vc_invite":
            await inter.response.send_modal(
                title="Пригласить участника",
                custom_id="modal_vc_invite",
                components=[
                    ui.Label(
                        "Пользователь сервера",
                        ui.UserSelect(
                            custom_id="select_vc_invite",
                            placeholder="Выберите пользователя...",
                        ),
                    )
                ],
            )

        # 6. Кикнуть (только среди участников в канале)
        elif custom_id == "vc_kick":
            members_in_channel = [m for m in channel.members if m.id != inter.author.id]
            if not members_in_channel:
                await inter.response.send_message("В канале никого нет, кроме вас.", ephemeral=True)
                return

            options = [
                disnake.SelectOption(label=m.display_name, value=str(m.id))
                for m in members_in_channel[:25]
            ]

            await inter.response.send_modal(
                title="Отключить участника",
                custom_id="modal_vc_kick",
                components=[
                    ui.Label(
                        "Участник для кика",
                        ui.StringSelect(
                            custom_id="select_vc_kick",
                            placeholder="Выберите участника из канала...",
                            options=options,
                        ),
                    )
                ],
            )

        # 7. Заблокировать (выбор среди всех пользователей сервера)
        elif custom_id == "vc_ban":
            await inter.response.send_modal(
                title="Заблокировать пользователя",
                custom_id="modal_vc_ban",
                components=[
                    ui.Label(
                        "Пользователь сервера",
                        ui.UserSelect(
                            custom_id="select_vc_ban",
                            placeholder="Выберите пользователя...",
                        ),
                    )
                ],
            )

    @commands.Cog.listener()
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        """Обработка подтверждения всех модальных окон."""
        channel = inter.channel
        if not isinstance(channel, disnake.VoiceChannel):
            return

        owner_id = await get_owner_by_channel_id(channel.id)
        if not owner_id or inter.author.id != owner_id:
            await inter.response.send_message("Вы не являетесь владельцем этой комнаты.", ephemeral=True)
            return

        # 1. Изменение названия
        if inter.custom_id == "modal_vc_rename":
            new_name = inter.text_values["input_vc_name"]
            await channel.edit(name=new_name)
            await update_voice_config(inter.author.id, "name", new_name)
            await inter.response.send_message(f"Название изменено на: **{new_name}**", ephemeral=True)

        # 2. Изменение лимита
        elif inter.custom_id == "modal_vc_limit":
            val = inter.text_values["input_vc_limit"]
            if not val.isdigit() or not (0 <= int(val) <= 99):
                await inter.response.send_message("Укажите корректное число от 0 до 99.", ephemeral=True)
                return

            limit = int(val)
            await channel.edit(user_limit=limit)
            await update_voice_config(inter.author.id, "user_limit", limit)
            await inter.response.send_message(
                f"Лимит участников установлен: **{limit if limit > 0 else 'Без ограничений'}**",
                ephemeral=True,
            )

        # 3. Передача прав
        elif inter.custom_id == "modal_vc_transfer":
            selected_ids = inter.values.get("select_vc_transfer", [])
            if not selected_ids:
                return

            target_id = int(selected_ids[0])
            new_owner = channel.guild.get_member(target_id)
            if not new_owner or new_owner.bot or new_owner.id == inter.author.id:
                await inter.response.send_message("Не удалось передать права выбранному пользователю.", ephemeral=True)
                return

            await update_voice_config(inter.author.id, "vc_channels_ids", None)
            await update_voice_config(new_owner.id, "vc_channels_ids", str(channel.id))

            await channel.set_permissions(new_owner, connect=True, view_channel=True, move_members=True)
            await inter.response.send_message(f"Владелец комнаты изменен на {new_owner.mention}.", ephemeral=True)

        # 4. Пригласить пользователя
        elif inter.custom_id == "modal_vc_invite":
            selected_ids = inter.values.get("select_vc_invite", [])
            if not selected_ids:
                return

            target_id = int(selected_ids[0])
            target = channel.guild.get_member(target_id)
            if not target:
                await inter.response.send_message("Пользователь не найден.", ephemeral=True)
                return

            await channel.set_permissions(target, connect=True, view_channel=True)
            await inter.response.send_message(f"Пользователю {target.mention} открыт доступ к комнате.", ephemeral=True)

        # 5. Кикнуть пользователя
        elif inter.custom_id == "modal_vc_kick":
            selected_ids = inter.values.get("select_vc_kick", [])
            if not selected_ids:
                return

            target_id = int(selected_ids[0])
            target = channel.guild.get_member(target_id)
            if target and target.voice and target.voice.channel == channel:
                await target.move_to(None)
                await inter.response.send_message(f"{target.mention} был отключен от комнаты.", ephemeral=True)
            else:
                await inter.response.send_message("Пользователь уже покинул канал.", ephemeral=True)

        # 6. Блокировка / Разблокировка пользователя
        elif inter.custom_id == "modal_vc_ban":
            selected_ids = inter.values.get("select_vc_ban", [])
            if not selected_ids:
                return

            target_id = int(selected_ids[0])
            target = channel.guild.get_member(target_id)
            if not target:
                await inter.response.send_message("Пользователь не найден.", ephemeral=True)
                return

            if target.id == inter.author.id:
                await inter.response.send_message("Нельзя взаимодействовать с самим собой.", ephemeral=True)
                return

            raw = await get_voice_config(inter.author.id, "blocked_users")
            blocked = json.loads(raw) if raw else []

            if target.id in blocked:
                # Разблокировка
                blocked.remove(target.id)
                await update_voice_config(inter.author.id, "blocked_users", json.dumps(blocked))
                await channel.set_permissions(target, overwrite=None)
                await inter.response.send_message(f"Пользователь {target.mention} **разблокирован**.", ephemeral=True)
            else:
                # Блокировка
                blocked.append(target.id)
                await update_voice_config(inter.author.id, "blocked_users", json.dumps(blocked))
                await channel.set_permissions(target, connect=False)
                if target in channel.members:
                    await target.move_to(None)
                await inter.response.send_message(f"Пользователь {target.mention} **заблокирован**.", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(VoiceChannelsCog(bot))