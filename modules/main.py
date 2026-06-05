import os
import re
import sys
import time
import requests

from aiohttp import ClientSession
from flask import Flask
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message
from subprocess import getstatusoutput
from threading import Thread

import core as helper
from vars import API_ID, API_HASH, BOT_TOKEN


app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running"


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


Thread(target=run_web_server, daemon=True).start()


bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


def parse_link_line(line):
    match = re.search(r"https?://\S+", line)
    if not match:
        return None

    url = match.group(0).strip()
    title = line[: match.start()].strip()
    title = title.rstrip(":-|").strip()
    if not title:
        title = "Video"

    return title, url


@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await m.reply_text(
        f"<b>Hello {m.from_user.mention}\n\n"
        "I am a bot for downloading links from your .TXT file and uploading them on Telegram.\n\n"
        "Use /upload to start.\n"
        "Use /stop to stop any ongoing task.</b>"
    )


@bot.on_message(filters.command("stop"))
async def restart_handler(_, m):
    await m.reply_text("**Stopped**", True)
    os.execl(sys.executable, sys.executable, *sys.argv)


@bot.on_message(filters.command(["upload"]))
async def upload(bot: Client, m: Message):
    editable = await m.reply_text("Send text file")
    input_file: Message = await bot.listen(editable.chat.id)
    x = await input_file.download()
    await input_file.delete(True)

    try:
        with open(x, "r", encoding="utf-8") as f:
            content = f.read()
        content = content.split("\n")
        links = []
        for item in content:
            parsed = parse_link_line(item.strip())
            if parsed:
                links.append(parsed)
        os.remove(x)
    except Exception:
        await m.reply_text("**Invalid file input.**")
        if os.path.exists(x):
            os.remove(x)
        return

    await editable.edit(
        f"**Total links found:** **{len(links)}**\n\n"
        "**Send the initial download number:** **1**"
    )
    input0: Message = await bot.listen(editable.chat.id)
