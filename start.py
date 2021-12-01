from telethon import TelegramClient, events, Button
from download_from_url import download_file, get_size
from file_handler import send_to_transfersh_async, progress, progressb
from progress_for_telethon import progress2
import json
import cryptg
import os
import time
import datetime
import aiohttp
import asyncio
import requests
from tools import execute
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from thumbnail_video import thumb_creator
from telethon.tl.types import DocumentAttributeVideo, DocumentAttributeAudio
import logging
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[logging.FileHandler('log.txt'), logging.StreamHandler()],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
#basicConfig(format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=INFO)
LOGGER = logging.getLogger(__name__)
#log: logging.Logger = logging.getLogger("FastTelethon")
logging.getLogger("telethon").setLevel(logging.WARNING)

api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
bot_token =os.environ.get("BOT_TOKEN")
# Array to store users who are authorized to use the bot
AUTH_USERS = set(int(x) for x in os.environ.get("AUTH_USERS", "").split())
                          
download_path = "Downloads/"

bot = TelegramClient('Encoder bot', api_id, api_hash).start(bot_token=bot_token)

HELP_TXT = """
I am a FFmpeg robot. I can convert All Type of Media.
for using me, you have to know about ffmpeg options.

the source and destination name must be deferent.
press /encode to start the proccess. then send your
media file or direct link. type your extension with ".".
`.mkv`
`_360p.mp4`
`_new.aac`
`2.mp3`.
and finaly type your ffmpeg options.

Examples:
Extract Audio without encoding:
`-vn -sn -c:a copy`

Extract Video without encoding:
`-sn -an -c:v copy`

mp3 bitrate 256k:
`-c:a libmp3lame -ab 256k`

trimm video - from minute 10 to minute 20:
`-ss 00:10:00 -to 00:20:00 -c copy`

mp4 + aac resolution 720*576
`-c:v libx264 -s 720*576 -c:a aac -ab 64k`
"""

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(f"Hi! Send /encode To Start.\n\nFor more info see /help")
    raise events.StopPropagation
    
@bot.on(events.NewMessage(pattern='/help'))
async def help(event):
    await event.respond(f"{HELP_TXT}")
    raise events.StopPropagation    

@bot.on(events.NewMessage(pattern='/encode'))
async def echo(update):
      
    ########################################################## Authorization
    
    user = await update.get_chat()
    if user.id not in AUTH_USERS:
        await update.reply("sorry ! you cant use this bot.\n\ndeploy your own bot:\n[Repository_Link](https://github.com/prxpostern/TGFFmpeg001)")
        return

    ########################################################## Step1
    
    msg1 = await update.respond(f"**Step1:** Send Your Media File or URL. \n\n To Cancel press /cancel")
    try:
        async with bot.conversation(update.message.chat_id) as cv:
            update2 = await cv.wait_event(events.NewMessage(update.message.chat_id))
    except Exception as e:
        print(e)
        await msg1.delete()
        await update.respond(f"**Conversation 1 Error:**\n\n{e}")
        return
    await msg1.delete()
    #u2 = str(update2)
    #u2 = json.loads(u2)
    LOGGER.info(f"{update2}")
    if update2.text == "/cancel":
        await update.respond(f"Operation Cancelled By User. \nSend /encode to Start Again!")
        return
    if not update2.message.message.startswith("/") and not update2.message.message.startswith("http") and update2.message.media:
        url_size = get_size(update2.message.document.size)
        url_fn = update2.message.message.media.document.file_name
        #url_fn = await update2.get_chat()
        #urlfn = json.loads(url_fn)
        LOGGER.info(f"{url_fn}")
    else:
        if "|" in update2.text:
            url , cfname = update2.text.split("|", 1)
            cfname = cfname.strip()
            filename = os.path.join(download_path, cfname)
        else:
            url = update2.text
            if os.path.splitext(url)[1]:
                filename = os.path.join(download_path, os.path.basename(url))
            else:
                await update2.reply("No Extension ! Use Custom Filename.")
                return
        url = url.strip()
        filename = filename.replace('%25','_')
        filename = filename.replace(' ','_')
        filename = filename.replace('%40','@')
        url_fn = os.path.basename(filename)
        r = requests.get(url, allow_redirects=True, stream=True)
        url_size = int(r.headers.get("content-length", 0))
        url_size = get_size(url_size)
    ########################################################## Step2

    msg2 = await update2.reply(f"`{url_fn}` [{url_size}]\n\n**Step2:** Enter The Extension : \n Examples: \n `_.mkv` \n `_320p.mp4` \n `_.mp3` \n `32k.aac` \n `_.m4a` \n\nTo Cancel press /cancel")
    try:
        async with bot.conversation(update.message.chat_id) as cv:
            ext1 = await cv.wait_event(events.NewMessage(update.message.chat_id))
    except Exception as e:
        print(e)
        await msg2.delete()
        await update.respond(f"**Conversation 2 Error:**\n\n{e}")
        return
    await msg2.delete()
    if ext1.text == "/cancel":
        await update.respond(f"Operation Cancelled By User. \nSend /encode to Start Again!")
        return
    
    ########################################################## Step3

    msg3 = await ext1.reply(
      f"`{url_fn}` [{url_size}]\n\n**Step3:** Enter FFmpeg Options: \n\n `-sn -vn -c:a copy` \n\n `-ar 48000 -ab 256k -f mp3` \n\n `-c:s copy -c:a copy -c:v libx264` \n\n `-c:v libx264 -s 320*240 -c:a libmp3lame -ar 48000 -ab 64k -f mp4` \n\nTo Cancel press /cancel"
    )
    try:
        async with bot.conversation(update.message.chat_id) as cv:
            ffcmd1 = await cv.wait_event(events.NewMessage(update.message.chat_id))
    except Exception as e:
        print(e)
        await update.respond(f"**Conversation 3 Error:**\n\n{e}")
        await msg3.delete()
        return
    await msg3.delete()
    if ffcmd1.text == "/cancel":
        await update.respond(f"Operation Cancelled By User. \nSend /encode to Start Again!")
        return
    
    ########################################################## Download
    
    msg4 = await update.respond(f"`Processing ...`")
    if not os.path.isdir(download_path):
        os.mkdir(download_path)
    if not update2.message.message.startswith("/") and not update2.message.message.startswith("http") and update2.message.media:
        await msg4.edit(f"**⬇️ Trying to Download Media ...**")
        start = time.time()
        file_path = await bot.download_media(update2.message, download_path, progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
            progress2(d, t, msg4, start, "⬇️ Downloading Status:")))
    else:
        start = time.time()
        try:
            file_path = await download_file(url, filename, msg4, start, bot)
        except Exception as e:
            print(e)
            await msg4.delete()
            await update.respond(f"Download Link is Invalid or Not Accessible !\n\n**Error:** {e}")
            try:
                os.remove(file_path)
            except:
                pass
            return
            
    print(f"file downloaded to {file_path}")
    await msg4.edit(f"✅ Successfully Downloaded.")
    await asyncio.sleep(1)
    ext2 = ext1.text
    ffcmd2 = ffcmd1.text
    ponlyname = os.path.splitext(file_path)[0]
    file_loc2 = f"{ponlyname}{ext2}"
    name = os.path.basename(file_loc2)
    ffcmd4 = f"ffmpeg -i \"{file_path}\" {ffcmd2} \"{file_loc2}\" -y"
    msg5 = await ffcmd1.reply(f"`{ffcmd4}` \n\n Encoding ... \n\n **PLZ Wait 😍 ...**")
    await asyncio.sleep(1)
    await msg4.delete()

    ########################################################## Encode
    
    out, err, rcode, pid = await execute(f"{ffcmd4}")
    if rcode != 0:
        print(err)
        await msg5.edit(f"**FFmpeg: Error Occured.**\n\n{err}")
        try:
            print("Deleted file :", file_path)
            os.remove(file_path)
            print("Deleted file :", file_loc2)
            os.remove(file_loc2)
        except:
            pass        
        return
    
    try:
        print("Deleted file :", file_path)
        os.remove(file_path)
    except:
        pass  
    
    ########################################################## Upload
    
    video_type = ['.mp4','.mkv','.avi','.webm','.wmv','.mov']
    vcheck = os.path.splitext(file_loc2)[1]
    if vcheck in video_type:
        thumbnail = await thumb_creator(file_loc2)
        thumbnail = str(thumbnail)
        metadata = extractMetadata(createParser(file_loc2))
        if metadata:
            duration = metadata.get("duration").seconds
            width = metadata.get("width")
            height = metadata.get("height")
    else:
        thumbnail = None
        metadata = extractMetadata(createParser(file_loc2))
        if metadata:
            duration = metadata.get("duration").seconds
    
    size = os.path.getsize(file_loc2)
    size = get_size(size)
    await msg5.edit(f"⬆️ Uploading to Telegram ... \n\n **Name: **`{name}`[{size_of_file}]")

    start = time.time()
    try:
        await bot.send_file(
            update.message.chat_id,
            file=str(file_loc2),
            thumb=thumbnail,
            caption=f"`{name}`\n\n**Size:** {size}",
            reply_to=update2.message,
            force_document=False,
            supports_streaming=True,
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(progress2(d, t, msg5, start, "⬆️ Uploading Status:", file=str(file_loc2)))
        )
    except Exception as e:
        print(e)
        await update.respond(f"❌ Uploading To Telegram Failed\n\n**Error:**\n{e}")
    finally:
        await msg5.delete()
        await update.respond(f"Send /encode to Start New Encoding")
        try:
            print("Deleted file :", file_loc2)
            os.remove(file_loc2)
        except:
            pass
    
    
#try:
#msg6 = await update.respond(f"⬆️ Uploading to `transfer.sh`... \n\n**Name: **`{name}`\n\n**Size:** {size_of_file}")
#download_link, final_date, size = await send_to_transfersh_async(file_loc2, msg6)
#await msg6.edit(f"✅ Successfully Uploaded to `Transfer.sh` !\n\n**Name: **`{name}`\n\n**Size:** {size}\n\n**Link:** `{download_link}` \n **ExpireDate:** {final_date}")
#except Exception as e:
#print(e)
#await update.respond(f"❌ Uploading to `TRANSFER.SH` Failed \n\n **Error:** {e}")

    
    

def main():
    """Start the bot."""
    print("\nBot started ...\n")
    bot.run_until_disconnected()

if __name__ == '__main__':
    main()
