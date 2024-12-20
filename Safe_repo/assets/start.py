import pymongo
from .. import bot as Safe_repo
from telethon import events, Button
from pyrogram import Client, filters
from telethon.tl.types import DocumentAttributeVideo
from multiprocessing import Process, Manager
import re
import logging
import pymongo
import sys
from pyrogram.types import Message
import math
import os
import yt_dlp
import time
from datetime import datetime as dt, timedelta
import json
import asyncio
import cv2
from yt_dlp import YoutubeDL
from telethon.sync import TelegramClient
from .. import sigma as app
from Safe_repo.assets.functions import screenshot
import subprocess
from config import MONGODB_CONNECTION_STRING, OWNER_ID, LOG_GROUP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "start_users"
COLLECTION_NAME = "registered_users_collection"

mongo_client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

def load_registered_users():
    registered_users = set()
    for user_doc in collection.find():
        registered_users.add(user_doc["user_id"])
    return registered_users

def save_registered_users(registered_users):
    for user_id in registered_users:
        collection.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

REGISTERED_USERS = load_registered_users()

@Safe_repo.on(events.NewMessage(pattern=f"^/start"))
async def start(event):
    """
    Command to start the bot
    """
    user_id = event.sender_id
    collection.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)
    buttons = [
        [Button.url("Join Channel", url="https://t.me/src_goku")],
        [Button.url("Contact Me", url="https://t.me/src_goku")],
    ]
    await Safe_repo.send_message(
        event.chat_id,
        message=TEXT,
        buttons=buttons
    )

@Safe_repo.on(events.NewMessage(pattern=f"^/gcast"))
async def broadcast(event):
    if event.sender_id != OWNER_ID:
        return await event.respond("You are not authorized to use this command.")

    message = event.message.text.split(' ', 1)[1]
    for user_doc in collection.find():
        try:
            user_id = user_doc["user_id"]
            await Safe_repo.send_message(user_id, message)
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {str(e)}")

def get_registered_users():
    registered_users = []
    for user_doc in collection.find():
        registered_users.append((str(user_doc["user_id"]), user_doc.get("first_name", "")))
    return registered_users

# Function to save user IDs and first names to a text file
def save_user_ids_to_txt(users_info, filename):
    with open(filename, "w") as file:
        for user_id, first_name in users_info:
            file.write(f"{user_id}: {first_name}\n")

@Safe_repo.on(events.NewMessage(incoming=True, pattern='/get'))
async def get_registered_users_command(event):
    # Check if the command is initiated by the owner
    if event.sender_id != OWNER_ID:
        return await event.respond("You are not authorized to use this command.")

    # Get all registered user IDs and first names
    registered_users = get_registered_users()

    # Save user IDs and first names to a text file
    filename = "registered_users.txt"
    save_user_ids_to_txt(registered_users, filename)

    # Send the text file
    await event.respond(file=filename, force_document=True)
    os.remove(filename)  # Remove the temporary file after sending

S = "/start"
TEXT = "Hey! I am Advance Content Saver Bot, do login in bot by /login and start saving from public/private channels/groups via sending post link.\n\n👉🏻 Execute /batch for bulk process upto 1K files range."


M = "/plan"
PRE_TEXT = """💰 **Premium Price**: Starting from $2 or 200 INR accepted via **__Amazon Gift Card__** (terms and conditions apply).
📥 **Download Limit**: Users can download up to 100 files in a single batch command.
🛑 **Batch**: You will get two modes /bulk and /batch.
   - Users are advised to wait for the process to automatically cancel before proceeding with any downloads or uploads.\n
📜 **Terms and Conditions**: For further details and complete terms and conditions, please send /terms.
"""

@Safe_repo.on(events.NewMessage(pattern=f"^{M}"))
async def plan_command(event):
    # Creating inline keyboard with buttons
    buttons = [
        [Button.url("Send Gift Card Code", url="https://t.me/src_gokubot")]
    ]

    # Sending photo with caption and buttons
    await Safe_repo.send_message(
        event.chat_id,
        message=PRE_TEXT,
        buttons=buttons
    )

T = "/terms"
TERM_TEXT = """📜 **Terms and Conditions** 📜\n
✨ We are not responsible for user deeds, and we do not promote copyrighted content. If any user engages in such activities, it is solely their responsibility.
✨ Upon purchase, we do not guarantee the uptime, downtime, or the validity of the plan. __Authorization and banning of users are at our discretion; we reserve the right to ban or authorize users at any time.__
✨ Payment to us **__does not guarantee__** authorization for the /batch command. All decisions regarding authorization are made at our discretion and mood.
"""

@Safe_repo.on(events.NewMessage(pattern=f"^{T}"))
async def term_command(event):
    # Creating inline keyboard with buttons
    buttons = [
        [Button.url("Query?", url="https://t.me/src_goku"),
         Button.url("Channel", url="https://telegram.dog/src_goku")]
    ]

    # Sending photo with caption and buttons
    await Safe_repo.send_message(
        event.chat_id,
        message=TERM_TEXT,
        buttons=buttons
    )

REPO_URL = "https://github.com/safe-repo/Save-Restricted-Content-Safe-Bot"

HELP_TEXT = """Here are the available commands:

➡️ /batch - to process link one by one iterating through single single message ids.

➡️ /dl - to download youtube videos.

➡️ /host - to download youtube videos.

➡️ /cancel - to cancel batches

➡️ /settings - to edit settings.

[GitHub Repository](%s)
""" % REPO_URL

# Purchase premium for more website supported repo and /adl repo.

@Safe_repo.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    buttons = [[Button.url("REPO", url=REPO_URL)]]
    await event.respond(HELP_TEXT, buttons=buttons, link_preview=False)


def thumbnail(chat_id):
    return f'{chat_id}.jpg' if os.path.exists(f'{chat_id}.jpg') else f'thumb.jpg'

# Function to get video info including duration
def get_youtube_video_info(url, cookies_path="youtube_cookies.json"):
    ydl_opts = {'quiet': True, 'skip_download': True}
    try:
      if os.path.exists(cookies_path):
        with open(cookies_path, "r") as f:
          cookies = json.load(f)
          ydl_opts['cookies'] = cookies
      with YoutubeDL(ydl_opts) as ydl:
          info_dict = ydl.extract_info(url, download=False)
          if not info_dict:
              return None
          return {
              'title': info_dict.get('title', 'Unknown Title'),
              'duration': info_dict.get('duration', 0),  # Duration in seconds
              'description':info_dict.get('description', '')
          }
    except Exception as e:
        logger.error(f"Error fetching video info: {e}")
        return None

def video_metadata(file):
    try:
        vcap = cv2.VideoCapture(f'{file}')
        if not vcap.isOpened():
            logger.error(f"Error: Could not open video file {file} for metadata extraction.")
            return {'width': 0, 'height': 0, 'duration': 0}

        width = round(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = round(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = vcap.get(cv2.CAP_PROP_FPS)
        frame_count = vcap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = round(frame_count / fps)

        vcap.release()  # Release the video capture
        return {'width': width, 'height': height, 'duration': duration}
    except Exception as e:
        logger.error(f"Error getting video metadata from {file}: {e}")
        return {'width': 0, 'height': 0, 'duration': 0}


# Function to extract recipe from description
def extract_recipe(description):
    if not description:
      return None

    # Basic regex to find ingredients and instructions
    ingredients_match = re.search(r"(ingredients|what you'll need|you will need):[\s\n]*(.*?)(?=instructions|method|how to cook|steps|procedure|$)", description, re.IGNORECASE | re.DOTALL)
    instructions_match = re.search(r"(instructions|method|how to cook|steps|procedure):[\s\n]*(.*)", description, re.IGNORECASE | re.DOTALL)

    ingredients = ""
    instructions = ""

    if ingredients_match:
        ingredients = ingredients_match.group(2).strip()
        # Split and clean each ingredient line
        ingredients = "\n".join([i.strip() for i in ingredients.split("\n") if i.strip() and not re.match(r"^[-–—•]$", i.strip())])

    if instructions_match:
       instructions = instructions_match.group(2).strip()
       instructions = "\n".join([i.strip() for i in instructions.split("\n") if i.strip() and not re.match(r"^[-–—•]$", i.strip())])

    if ingredients or instructions:
        return {
            'ingredients': ingredients,
            'instructions': instructions
        }
    else:
      return None


@app.on_message(filters.command("dl", prefixes="/"))
async def youtube_dl_command(_, message):
    # Check if the command has an argument (YouTube URL)
    if len(message.command) > 1:
        youtube_url = message.command[1]

        # Send initial message indicating downloading
        progress_message = await message.reply("Fetching video info...")

        try:
            # Fetch video info using yt-dlp
            video_info = get_youtube_video_info(youtube_url)
            if not video_info:
                await progress_message.edit_text("Failed to fetch video info.")
                return

            # Check if video duration is greater than 3 hours (10800 seconds)
            if video_info['duration'] > 10800:
                await progress_message.edit_text("Video duration exceeds 3 hours. Not allowed.")
                return
            
            # Extract Recipe
            recipe = extract_recipe(video_info.get('description', ''))
            if recipe:
              await progress_message.reply(f"__Recipe:__\n\n__**Ingredients:**__\n{recipe.get('ingredients')}\n\n__**Instructions:**__\n{recipe.get('instructions')}")

            # Send buttons for quality selection
            buttons = [
              [Button.inline("Best Quality", data=f"dl_best_{youtube_url}"),
               Button.inline("Medium Quality", data=f"dl_medium_{youtube_url}")],
              [Button.inline("Low Quality", data=f"dl_low_{youtube_url}")]
           ]

            await progress_message.edit_text("Choose quality:", buttons=buttons)

        except Exception as e:
            logger.error(f"Error during /dl command: {e}")
            await progress_message.edit_text(f"An error occurred: {str(e)}")

    else:
        await message.reply("Please provide a YouTube URL after /dl.")


@app.on_callback_query(filters.regex("^dl_(best|medium|low)_"))
async def youtube_dl_callback(_, query):
    quality, youtube_url = query.data.split('_', 2)[1:]

    # Send initial message indicating downloading
    progress_message = await query.message.edit_text(f"Downloading video in {quality} quality...")

    try:
        # Fetch video info using yt-dlp
        video_info = get_youtube_video_info(youtube_url)
        if not video_info:
            await progress_message.edit_text("Failed to fetch video info.")
            return

        # Check if video duration is greater than 3 hours (10800 seconds)
        if video_info['duration'] > 10800:
            await progress_message.edit_text("Video duration exceeds 3 hours. Not allowed.")
            return

        # Safe file naming
        original_file = f"{video_info['title'].replace('/', '_').replace(':', '_')}.mp4"
        thumbnail_path = f"{video_info['title'].replace('/', '_').replace(':', '_')}.jpg"

        # Define download format based on quality
        if quality == 'best':
            download_format = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        elif quality == 'medium':
            download_format = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]"
        else:  # Low quality
            download_format = "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best[height<=360]"

        # Download video
        ydl_opts = {
            'format': download_format,
            'outtmpl': original_file,
            'noplaylist': True,
            'quiet':True
        }
        try:
            with open("youtube_cookies.json", "r") as f:
                cookies = json.load(f)
            ydl_opts['cookies'] = cookies
        except FileNotFoundError:
              await progress_message.edit_text("`youtube_cookies.json` not found. Please create it. See /help for more.")
              return

        with YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([youtube_url])
            except yt_dlp.utils.DownloadError as e:
                if "Sign in to confirm you're not a bot" in str(e):
                   await progress_message.edit_text("`yt-dlp` failed. Please update the cookie. See /help for more.")
                   return
                else:
                    logger.error(f"yt-dlp DownloadError: {e}")
                    await progress_message.edit_text(f"Failed to download the video.  {e}")
                    return
            except Exception as e:
                logger.error(f"yt-dlp error during download: {e}")
                await progress_message.edit_text(f"Failed to download the video due to {e}")
                return

        # Check if the original file exists before renaming
        if not os.path.exists(original_file):
             await progress_message.edit_text("Failed to download video.")
             return

        # Edit the progress message to indicate uploading
        await progress_message.edit_text("Uploading video...")

        # Get video metadata
        metadata = video_metadata(original_file)
        caption = f"{video_info['title']}\n\n__**Powered by [SRC Bot](https://t.me/src_goku)**__"  # Set caption to the title of the video

        # Send the video file and thumbnail
        safe_repo_bot = query.message.chat.id
        k = thumbnail(safe_repo_bot)
        result = await app.send_video(
            chat_id=query.message.chat.id,
            video=original_file,
            caption=caption,
            thumb=k,
            width=metadata['width'],
            height=metadata['height'],
            duration=metadata['duration'],
        )
        await result.copy(LOG_GROUP)

        os.remove(original_file)

        # Delete the progress message after sending video
        await progress_message.delete()

    except Exception as e:
        logger.error(f"Error during callback: {e}")
        await progress_message.edit_text(f"An error occurred: {str(e)}")


def video_metadata(file):
    vcap = cv2.VideoCapture(f'{file}')
    width = round(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = round(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = vcap.get(cv2.CAP_PROP_FPS)
    frame_count = vcap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = round(frame_count / fps)
    return {'width': width, 'height': height, 'duration': duration}