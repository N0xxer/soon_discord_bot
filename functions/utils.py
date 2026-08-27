import disnake


def create_embed(
    title: str, 
    description: str = None, 
    color: disnake.Color = disnake.Color.blue(),
    footer_text: str = None
) -> disnake.Embed:
    """Универсальная функция для создания красивых Embed-сообщений."""
    embed = disnake.Embed(
        title=title,
        description=description,
        color=color
    )
    if footer_text:
        embed.set_footer(text=footer_text)
    return embed


def format_number(number: int) -> str:
    """Форматирует числа с разделителями (например, 1000000 -> 1 000 000)."""
    return f"{number:,}".replace(",", " ")