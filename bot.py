import logging
import os
import re
import asyncio
import discord
from discord import app_commands
from dotenv import load_dotenv

from db import Database
import queries as Q

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "minecraft")

logging.basicConfig(level=logging.INFO)
if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")

intents = discord.Intents.none()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

db = Database(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)


def strip_mc_colors(s: str) -> str:
    if not s:
        return s
    s = re.sub(r"&\#[0-9a-fA-F]{6}", "", s)
    s = re.sub(r"&[0-9a-fk-orA-FK-OR]", "", s)
    return s.strip()


def team_display(team: str | None, display_raw: str | None) -> str:
    if team is None or team == "":
        return "No team"
    if display_raw:
        clean = strip_mc_colors(display_raw)
        return clean if clean else team
    return team
    
@client.event
async def on_ready():
    print("READY: bot connected to Discord")
    try:
        await asyncio.wait_for(db.connect(), timeout=10)
        print("READY: db connected")
    except Exception as e:
        print("READY: db connect FAILED:", repr(e))
        return

    guild = discord.Object(id=GUILD_ID) if GUILD_ID else None
    if guild:
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)
        print("READY: commands synced to guild", GUILD_ID)
    else:
        await tree.sync()
        print("READY: commands synced globally")

    print(f"✅ Logged in as {client.user}")


@tree.command(name="player", description="Информация об игроке по нику")
@app_commands.describe(name="Ник игрока")
async def player_cmd(interaction: discord.Interaction, name: str):
    await interaction.response.defer(thinking=True)

    row = await db.fetch_one(Q.GET_PLAYER_BY_NAME, (name,))
    if not row:
        await interaction.followup.send(f"Игрок **{name}** не найден в базе данных.")
        return

    kills = int(row.get("kills", 0) or 0)
    team = row.get("team")
    display_raw = row.get("display_raw")
    updated_at = row.get("updated_at")

    emb = discord.Embed(title=f"👤 {row.get('name')}", color=0x2b2d31)
    emb.add_field(name="Команда: ", value=team_display(team, display_raw), inline=True)
    emb.add_field(name="Убийств: ", value=str(kills), inline=True)

    skin_url = f"https://mc-heads.net/body/{row.get('name')}/200"
    emb.set_image(url=skin_url)

    if updated_at is not None:
        emb.add_field(name="Updated", value=str(updated_at), inline=True)

    await interaction.followup.send(embed=emb)


@tree.command(name="team", description="Информация о команде")
@app_commands.describe(team="Системное имя команды (например number9, interlinx). Можете уточнить у администрации.")
async def team_cmd(interaction: discord.Interaction, team: str):
    await interaction.response.defer(thinking=True)

    info = await db.fetch_one(Q.GET_TEAM_INFO, (team,))
    if not info:
        await interaction.followup.send(f"Команда **{team}** не найдена.")
        return

    members = await db.fetch_all(Q.GET_TEAM_MEMBERS, (team,))
    disp = team_display(info.get("team"), info.get("display_raw"))

    emb = discord.Embed(title=f"🛡 Команда: {disp}", color=0x2b2d31)
    emb.add_field(name="Участников: ", value=str(int(info.get("members", 0) or 0)), inline=True)
    emb.add_field(name="Убийств (В сумме): ", value=str(int(info.get("kills", 0) or 0)), inline=True)

    if members:
        lines = []
        for i, m in enumerate(members[:15], start=1):
            lines.append(f"{i}. **{m['name']}** - {int(m.get('kills', 0) or 0)} K")
        emb.add_field(name="Топ участников", value="\n".join(lines), inline=False)

    await interaction.followup.send(embed=emb)


@tree.command(name="topteams", description="Топ команд по киллам")
async def topteams_cmd(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    limit = 10

    rows = await db.fetch_all(Q.TOP_TEAMS_BY_KILLS, (limit,))
    if not rows:
        await interaction.followup.send("В базе нет команд для топа.")
        return

    emb = discord.Embed(title=f"🏆 Топ 10 команд по киллам в текущем сезоне:", color=0x2b2d31)
    desc = []
    for i, r in enumerate(rows, start=1):
        team = r.get("team") or "—"
        disp = team_display(team, r.get("display_raw"))
        kills = int(r.get("kills", 0) or 0)
        members = int(r.get("members", 0) or 0)
        desc.append(f"**{i}. {disp}** — {kills} убийств | {members} участников")
    emb.description = "\n".join(desc)

    await interaction.followup.send(embed=emb)


@tree.command(name="topplayers", description="Топ игроков по киллам")
@app_commands.describe(limit="Сколько игроков показать (1-20)")
async def topplayers_cmd(interaction: discord.Interaction, limit: int = 10):
    await interaction.response.defer(thinking=True)
    limit = max(1, min(20, limit))

    rows = await db.fetch_all(Q.TOP_PLAYERS_BY_KILLS, (limit,))
    if not rows:
        await interaction.followup.send("В базе нет игроков для топа.")
        return

    emb = discord.Embed(title=f"🏅 Топ {limit} игроков по киллам в текущем сезоне!", color=0x2b2d31)
    lines = []
    for i, r in enumerate(rows, start=1):
        name = r.get("name") or "—"
        kills = int(r.get("kills", 0) or 0)
        disp = team_display(r.get("team"), r.get("display_raw"))
        lines.append(f"**{i}. {name}** — {kills} K ({disp})")
    emb.description = "\n".join(lines)

    await interaction.followup.send(embed=emb)


async def main():
    await client.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
