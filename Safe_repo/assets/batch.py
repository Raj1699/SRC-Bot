import time
import os
import logging
import json
from .. import bot as Safe_repo
from .. import defaultbot
from .. import Bot
from telethon import events, Button, errors
from pyrogram.errors import FloodWait
from Safe_repo.assets.pyroplug import check, get_bulk_msg
from Safe_repo.assets.functions import get_link
from Safe_repo.assets.login import get_session
import asyncio
from pyrogram import Client 
from config import API_ID, API_HASH, MONGODB_CONNECTION_STRING
import pymongo

# Logger is already configured in __main__
logger = logging.getLogger(__name__)

# MongoDB Connection
mongo_client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
db = mongo_client["batch_data_db"]
batch_collection = db["batch_data"]
ids_collection = db["ids_data"]

# --------------------- BATCH BEGINS ------------------ 

def save_batch_data(user_id, status):
    batch_collection.update_one(
        {"user_id": str(user_id)},
        {"$set": {"status": status}},
        upsert=True
    )

def load_batch_data(user_id):
    data = batch_collection.find_one({"user_id": str(user_id)})
    return data["status"] if data else False

def delete_batch_data(user_id):
    batch_collection.delete_one({"user_id": str(user_id)})

def save_ids_data(user_id, ids_list):
    ids_collection.update_one(
        {"user_id": str(user_id)},
        {"$set": {"ids_list": ids_list}},
        upsert=True
    )

def load_ids_data(user_id):
    data = ids_collection.find_one({"user_id": str(user_id)})
    return data["ids_list"] if data else []

def delete_ids_data(user_id):
    ids_collection.delete_one({"user_id": str(user_id)})


@Safe_repo.on(events.NewMessage(incoming=True, pattern='/batch'))
async def _batch(event):
    user_id = event.sender_id
    userbot = None

    # Check for user session
    session_data = get_session(user_id)
    if session_data:
        try:
            userbot = Client(":userbot:", api_id=API_ID, api_hash=API_HASH, session_string=session_data)
            await userbot.start()
        except Exception as e:
            await event.respond("Your session might be expired /logout and again do /login or simply logout and send link...")
    else:
      userbot = defaultbot

    if load_batch_data(user_id):
        return await event.reply("You've already started one batch, wait for it to complete!")

    async with Safe_repo.conversation(event.chat_id) as conv: 
        try:
            await conv.send_message(f"Send me the message link you want to start saving from, as a reply to this message.", buttons=Button.force_reply())
            link = await conv.get_reply()
            try:
                _link = get_link(link.text)
            except Exception:
                await conv.send_message("No link found...")
                return
            await conv.send_message(f"Send me the number of files/range you want to save from the given message, as a reply to this message.", buttons=Button.force_reply())
            _range = await conv.get_reply()
            try:
                value = int(_range.text)
                if value > 100000:
                    return await conv.send_message("You can only get up to 100000 files in a single batch.\n\nPurchase premium to go beyong limit send /plan to know more...")
            except ValueError:
                return await conv.send_message("Range must be an integer!")

            save_ids_data(user_id, list(range(value)))

            s, r = await check(userbot, Bot, _link, event)
            if s != True:
                await conv.send_message(r)
                return

            save_batch_data(user_id, True)
            

            cd = await conv.send_message("**Batch process ongoing...**\n\nProcess completed: ", 
                                    buttons=[[Button.url("Join Channel", url="http://t.me/src_goku")]])
            co = await run_batch(userbot, Bot, user_id, cd, _link) 
            try: 
                if co == -2:
                    await Bot.send_message(user_id, "Batch successfully completed!")
                    await cd.edit(f"**Batch process ongoing.**\n\nProcess completed: {value} \n\n Batch successfully completed! ")
            except:
                await Bot.send_message(user_id, "ERROR!\n\n maybe last msg didn't exist yet")
            finally:
                conv.cancel()
                delete_batch_data(user_id)
                delete_ids_data(user_id)
        except Exception as e:
            logger.info(e)
            await conv.send_message("Processed")

@Safe_repo.on(events.NewMessage(incoming=True, pattern='/cancel'))
async def cancel_command(event):
    user_id = event.sender_id
    if load_ids_data(user_id):
        delete_ids_data(user_id)
        await event.respond("Operation canceled.")
    else:
        await event.respond("There is no operation to cancel.")


async def run_batch(userbot, client, sender, countdown, link):
    ids_list = load_ids_data(sender)
    for i in range(len(ids_list)):
        # Check if cancelled
        if not load_ids_data(sender):
             break

        timer = 15  # Increased default timer value

        if i < 250:
            timer = 20
        elif 250 <= i < 1000:
            timer = 25
        elif 1000 <= i < 10000:
            timer = 30
        elif 10000 <= i < 50000:
            timer = 35
        elif 50000 <= i < 100000:
            timer = 40
        elif 100000 <= i < 200000:
            timer = 45
        elif i >= 200000:
            timer = 60  # Increased timer value for larger counts

        # Adjust the timer for links other than channel links
        if 't.me/c/' not in link:
            timer = 10 if i < 500 else 30  # Increased timer values for non-channel links

        try: 
            count_down = f"**Batch process ongoing.**\n\nProcess completed: {i+1}"
            integer = int(link.split("/")[-1]) + int(ids_list[i])
            await get_bulk_msg(userbot, client, sender, link, integer)
            protection = await client.send_message(sender, f"Sleeping for `{timer}` seconds to avoid Floodwaits and Protect account!")
            await countdown.edit(count_down, 
                                 buttons=[[Button.url("Join Channel", url="https://t.me/src_goku")]])
            await asyncio.sleep(timer)
            await protection.delete()
        except IndexError as ie:
            await client.send_message(sender, f" {i}  {ie}  \n\nBatch ended completed!")
            await countdown.delete()
            break
        except FloodWait as fw:
            if int(fw.value) > 300:
                await client.send_message(sender, f'You have floodwaits of {fw.value} seconds, cancelling batch') 
                delete_ids_data(sender)
                break
            else:
                fw_alert = await client.send_message(sender, f'Sleeping for {fw.value + 15} second(s) due to Telegram floodwait.')
                ors = fw.value + 5
                await asyncio.sleep(ors)
                await fw_alert.delete()
                try:
                    await get_bulk_msg(userbot, client, sender, link, integer)
                except Exception as e:
                    logger.info(e)
                    if countdown.text != count_down:
                        await countdown.edit(count_down, buttons=[[Button.url("Join Channel", url="http://t.me/src_goku")]])
        except Exception as e:
            #logger.info(e)
            #await client.send_message(sender, f"An error occurred during cloning, batch will continue.\n\n**Error:** {str(e)}")
            if countdown.text != count_down:
                await countdown.edit(count_down, buttons=[[Button.url("Join Channel", url="https://t.me/src_goku")]])
        n = i + 1
        if n == len(ids_list):
            return -2
