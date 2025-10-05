import logging
import yt_dlp
import random
import os
import math
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# -----------------------------------------------------------------
# --- বট টোকেন এবং আইডি ---
# -----------------------------------------------------------------
TOKEN_FILE_ROAST = "8092296730:AAG81mthVR-4VbmleBoY9AeN28PvDmj7RW8"
TOKEN_MUSIC_UPLOADER = "8159877922:AAGB7LE3YPZ_vvFAxiapWn-t-8cZr9r3Lic"
TOKEN_NEDHAS_DOWNLOADER = "8025249470:AAHHDoZ2ugl7zgn20FRnYS58ElrzkdGFlnA"
TOKEN_CAPTION_BOT = "8234759585:AAF8hMnSTEWmix7V0s8XlVb-XeDRRQXk2I8"

CHANNEL_ID_MUSIC = -1002178292415
CHANNEL_ID_CAPTION = -1002345545776
# -----------------------------------------------------------------

# --- সাধারণ কনফিগারেশন এবং লগিং ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# =================================================================
# ===== সেকশন ১: File Roast Bot এর ফাংশন =====
# =================================================================
async def upload_to_gofile_async(file_path):
    def _upload():
        server_response = requests.get('https://api.gofile.io/servers')
        server_response.raise_for_status()
        server = server_response.json()['data']['servers'][0]['name']
        with open(file_path, 'rb') as f:
            upload_response = requests.post(f"https://{server}.gofile.io/uploadFile", files={'file': f})
            upload_response.raise_for_status()
        return upload_response.json().get('data', {}).get('downloadPage')
    try:
        return await asyncio.to_thread(_upload)
    except Exception as e:
        logger.error(f"GoFile Upload Error: {e}")
        return None

async def start_file_roast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"👋 হ্যালো {user_name}!\n\nআমি ফাইল টু লিংক জেনারেটর বট।\nDeveloper: @annonymous707")

async def handle_file_roast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_attachment = update.message.document or (update.message.photo[-1] if update.message.photo else None) or update.message.video or update.message.audio
    if not file_attachment: return
    
    processing_message, local_file_path_obj = None, None
    try:
        processing_message = await update.message.reply_text("ফাইল পেয়েছি, আপলোড করছি... ⏳")
        file = await context.bot.get_file(file_attachment.file_id)
        suggested_filename = getattr(file_attachment, 'file_name', None) or os.path.basename(file.file_path)
        local_file_path_obj = await file.download_to_drive(custom_path=suggested_filename)
        
        download_link = await upload_to_gofile_async(local_file_path_obj.name)
        
        if download_link:
            success_message = f"✅ আপলোড সফল!\n\n🔗 আপনার লিংক:\n`{download_link}`\n\n*(লিংকটি কপি করতে ট্যাপ করুন)*\n\nDeveloper: @annonymous707"
            keyboard = [[InlineKeyboardButton("📂 নতুন ফাইল পাঠাবো", callback_data='send_new_file')]]
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_message.message_id)
            await update.message.reply_text(success_message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await context.bot.edit_message_text("❌ আপলোড ব্যর্থ হয়েছে।", chat_id=update.effective_chat.id, message_id=processing_message.message_id)
    except Exception as e:
        logger.error(f"File Roast Error: {e}")
    finally:
        if local_file_path_obj and await asyncio.to_thread(os.path.exists, local_file_path_obj.name):
            await asyncio.to_thread(os.remove, local_file_path_obj.name)

async def button_callback_file_roast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'send_new_file': await query.message.reply_text("অনুগ্রহ করে আপনার নতুন ফাইলটি পাঠান।")

# =================================================================
# ===== সেকশন ২: Music Uploader Bot এর ফাংশন =====
# =================================================================
SEARCH_QUERIES_MUSIC = ["zubeen garg song viral", "Latest Bengali Official Audio Song", "Hindi old viral song", "Bangla old song", "Runa Laila Song", "Andrew Kishore viral song", "kk viral song", "sreya ghosal viral song", "arman Malik song", "monali Thakur viral song", "arman Malik song", "tanveer Evan song viral", "t series song", "Eagle music song", "svf music", "Top Bollywood Single Track This Week"]
DEVELOPER_CREDIT_MUSIC = "\n\n🎶 Credit: @music__uplader__bot\n👨‍💻 Developer: @annonymous707\n\n**[ A Product Of Team SP ]**"
posted_video_ids = set()
DOWNLOAD_DIR_MUSIC = "music_downloads"
if not os.path.exists(DOWNLOAD_DIR_MUSIC): os.makedirs(DOWNLOAD_DIR_MUSIC)

def find_and_download_song_blocking():
    try:
        ydl_opts_search = {'format': 'bestaudio/best', 'quiet': True, 'default_search': 'ytsearch10', 'noplaylist': True, 'match_filter': yt_dlp.utils.match_filter_func('duration < 600')}
        with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
            search_result = ydl.extract_info(random.choice(SEARCH_QUERIES_MUSIC), download=False)
        valid_entries = [e for e in search_result.get('entries', []) if e and e.get('id') not in posted_video_ids]
        if not valid_entries: return None
        video_to_download = random.choice(valid_entries)
        ydl_opts_download = {'format': 'bestaudio/best', 'outtmpl': os.path.join(DOWNLOAD_DIR_MUSIC, '%(title)s.%(ext)s'), 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]}
        with yt_dlp.YoutubeDL(ydl_opts_download) as ydl: ydl.download([video_to_download['webpage_url']])
        posted_video_ids.add(video_to_download.get('id'))
        original_filename = ydl.prepare_filename(video_to_download)
        mp3_filename = os.path.splitext(original_filename)[0] + '.mp3'
        if os.path.exists(mp3_filename):
            return {'path': mp3_filename, 'info': video_to_download}
    except Exception as e:
        logger.error(f"Music Uploader blocking task error: {e}")
    return None

async def post_song_job(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    song_data = await asyncio.to_thread(find_and_download_song_blocking)
    if not song_data: return
    file_path, video_info = song_data['path'], song_data['info']
    try:
        if await asyncio.to_thread(os.path.getsize, file_path) > 50 * 1024 * 1024: return
        final_caption = f"🎧 **{video_info.get('title', 'N/A')}**\n🎤 Artist: {video_info.get('artist') or video_info.get('uploader', 'N/A')}" + DEVELOPER_CREDIT_MUSIC
        with open(file_path, 'rb') as audio_file:
            await bot.send_audio(chat_id=CHANNEL_ID_MUSIC, audio=audio_file, title=video_info.get('title', 'N/A'), performer=video_info.get('artist', 'N/A'), duration=video_info.get('duration', 0), caption=final_caption, parse_mode='Markdown')
        logger.info(f"Music Uploader: ✅ গান পোস্ট করা হয়েছে - {video_info.get('title')}")
    except Exception as e:
        logger.error(f"Music Uploader send error: {e}")
    finally:
        if await asyncio.to_thread(os.path.exists, file_path):
            await asyncio.to_thread(os.remove, file_path)

# =================================================================
# ===== সেকশন ৩: Nedhas Downloader Bot এর ফাংশন =====
# =================================================================
def format_duration(seconds):
    if seconds is None: return ""
    m, s = divmod(seconds, 60)
    return f"{int(m):02d}:{int(s):02d}"

async def send_welcome_message_nedhas(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user: User):
    welcome_message = f"🌟 **স্বাগতম, {user.mention_html()}!** 🌟\n\nআমি মিডিয়া ডাউনলোডার। আমাকে যেকোনো ভিডিওর লিঙ্ক পাঠান।\n\n👨‍💻 **ডেভেলপার:** PARV3Z"
    await context.bot.send_message(chat_id, welcome_message, parse_mode='HTML', disable_web_page_preview=True)
    context.user_data['messages_to_delete'] = []

async def start_nedhas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_welcome_message_nedhas(context, update.effective_chat.id, update.effective_user)

async def handle_link_nedhas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video_url = update.message.text.strip()
    processing_message = await update.message.reply_text("🔍 **লিঙ্কটি বিশ্লেষণ করা হচ্ছে...**")
    def _extract_info():
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl: return ydl.extract_info(video_url, download=False)
    try:
        info_dict = await asyncio.to_thread(_extract_info)
        formats, available_formats, best_audio = info_dict.get('formats', [info_dict]), {}, None
        for f in formats:
            if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                if best_audio is None or f.get('abr', 0) > best_audio.get('abr', 0): best_audio = f
            if f.get('vcodec') != 'none' and f.get('height'):
                resolution, filesize = f['height'], f.get('filesize') or f.get('filesize_approx')
                if resolution not in available_formats: available_formats[resolution] = {'format_id': f['format_id'], 'filesize': filesize}
        if not available_formats and not best_audio:
            await processing_message.edit_text('❌ কোনো ডাউনলোডযোগ্য ফরম্যাট খুঁজে পাওয়া যায়নি।'); return
        keyboard, row = [], []
        if best_audio:
            filesize = best_audio.get('filesize') or best_audio.get('filesize_approx')
            size_str = f"{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
            keyboard.append([InlineKeyboardButton(f"🎧 MP3 অডিও ({size_str})", callback_data=f"audio|{video_url}")])
        for res in sorted(available_formats.keys(), reverse=True):
            data, filesize = available_formats[res], available_formats[res]['filesize']
            size_str = f"{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
            row.append(InlineKeyboardButton(f"🎬 {res}p ({size_str})", callback_data=f"{data['format_id']}|{video_url}"))
            if len(row) == 2: keyboard.append(row); row = []
        if row: keyboard.append(row)
        await processing_message.edit_text('✅ আপনার পছন্দের অপশনটি বেছে নিন:', reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await processing_message.edit_text(f'❌ লিঙ্কটি প্রসেস করা সম্ভব হয়নি।\n`কারণ: {e}`', parse_mode='Markdown')

async def button_callback_nedhas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query, filename = update.callback_query, None
    await query.answer()
    data, video_url = query.data.split('|', 1)
    status_message = await query.message.reply_text("📥 **ডাউনলোড শুরু হচ্ছে...**")
    def _download_and_get_path():
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl: meta = ydl.extract_info(video_url, download=False)
        video_title, duration_str = meta.get('title', 'N/A'), format_duration(meta.get('duration'))
        output_template = f'downloads_nedhas/%(title)s-{query.id}.%(ext)s'
        ydl_opts = {'outtmpl': output_template, 'quiet': True, 'no_warnings': True}
        if data == 'audio':
            ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]})
        else: ydl_opts['format'] = f'{data}+bestaudio/best'
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            info = ydl.extract_info(video_url, download=False)
            base_filename = ydl.prepare_filename(info)
        if data == 'audio': final_filename = os.path.splitext(base_filename)[0] + '.mp3'
        else:
            final_filename = None
            for ext in ['.mp4', '.mkv', '.webm']:
                potential_filename = os.path.splitext(base_filename)[0] + ext
                if os.path.exists(potential_filename): final_filename = potential_filename; break
            if not final_filename: final_filename = base_filename
        return final_filename, video_title, duration_str
    try:
        await asyncio.to_thread(os.makedirs, 'downloads_nedhas', exist_ok=True)
        filename, video_title, duration_str = await asyncio.to_thread(_download_and_get_path)
        if not await asyncio.to_thread(os.path.exists, filename): raise FileNotFoundError("ডাউনলোড করা ফাইল খুঁজে পাওয়া যায়নি!")
        file_size_mb = await asyncio.to_thread(os.path.getsize, filename) / (1024 * 1024)
        if file_size_mb > 49:
            await status_message.edit_text(f"⚠️ ফাইলটির আকার ({file_size_mb:.2f} MB) 50MB এর বেশি।")
        else:
            await status_message.edit_text(text="📤 ফাইলটি আপলোড করা হচ্ছে...")
            caption = f"✅ **কাজ সম্পন্ন!**\n\n🎬 **শিরোনাম:** {video_title}\n⏱️ **দৈর্ঘ্য:** {duration_str}\n\n👨‍💻 **ডেভেলপার:** PARV3Z"
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("✨ নতুন ডাউনলোড", callback_data="refresh_new_link")]])
            with open(filename, 'rb') as file_to_send:
                if data == 'audio': await context.bot.send_audio(chat_id=query.message.chat_id, audio=file_to_send, caption=caption, parse_mode='HTML', reply_markup=reply_markup)
                else: await context.bot.send_video(chat_id=query.message.chat_id, video=file_to_send, caption=caption, parse_mode='HTML', reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Nedhas Download/Upload Error: {e}")
        await status_message.edit_text(f"❌ **একটি সমস্যা হয়েছে:**\n`{e}`", parse_mode='Markdown')
    finally:
        if filename and await asyncio.to_thread(os.path.exists, filename): await asyncio.to_thread(os.remove, filename)

async def refresh_callback_nedhas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    message_ids = context.user_data.get('messages_to_delete', [])
    if query.message: message_ids.append(query.message.message_id)
    for msg_id in set(message_ids):
        try: await context.bot.delete_message(chat_id=query.message.chat_id, message_id=msg_id)
        except BadRequest: pass
    await send_welcome_message_nedhas(context, query.message.chat_id, query.from_user)

# =================================================================
# ===== সেকশন ৪: Caption Bot এর ফাংশন =====
# =================================================================
def scrape_captions_blocking():
    all_captions = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    urls = ["https://bestcaptionbangla.com/", "https://banglacaption.blog/"]
    for url in urls:
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            if "bestcaptionbangla" in url: all_captions.extend([p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 20 and 'ক্যাপশন' not in p.get_text(strip=True)])
            elif "banglacaption.blog" in url: all_captions.extend([p.get_text(strip=True) for b in soup.find_all('blockquote', class_='wp-block-quote') if (p := b.find('p'))])
        except Exception as e: logger.error(f"Caption Scrape Error for {url}: {e}")
    return all_captions

async def post_caption_job(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    captions = await asyncio.to_thread(scrape_captions_blocking)
    if captions:
        try:
            await bot.send_message(chat_id=CHANNEL_ID_CAPTION, text="🔥")
            await asyncio.sleep(1)
            await bot.send_message(chat_id=CHANNEL_ID_CAPTION, text=random.choice(captions))
            logger.info("Caption Bot: ✅ ক্যাপশন পোস্ট করা হয়েছে।")
        except Exception as e: logger.error(f"Caption Bot Error: {e}")

async def handle_private_message_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("অনুগ্রহপূর্বক মেসেজ দিয়ে বিরক্ত করবেন না।\nযোগাযোগ করুন @annonymous707 এর সাথে।")

# =================================================================
# ===== মূল Asyncio রানার: ৪টি বট একসাথে চালানোর জন্য =====
# =================================================================
async def main():
    # --- প্রতিটি বটের জন্য Application অবজেক্ট তৈরি করা ---
    app_file_roast = Application.builder().token(TOKEN_FILE_ROAST).build()
    app_music_uploader = Application.builder().token(TOKEN_MUSIC_UPLOADER).build()
    app_nedhas = Application.builder().token(TOKEN_NEDHAS_DOWNLOADER).build()
    app_caption = Application.builder().token(TOKEN_CAPTION_BOT).build()
    
    apps = [app_file_roast, app_music_uploader, app_nedhas, app_caption]

    # --- প্রতিটি বটের জন্য হ্যান্ডলার এবং জব সেটআপ করা ---
    # বট ১: File Roast Bot
    app_file_roast.add_handler(CommandHandler("start", start_file_roast))
    app_file_roast.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO, handle_file_roast))
    app_file_roast.add_handler(CallbackQueryHandler(button_callback_file_roast))

    # বট ২: Music Uploader Bot
    app_music_uploader.job_queue.run_repeating(post_song_job, interval=3 * 60, first=5)

    # বট ৩: Nedhas Downloader Bot
    app_nedhas.add_handler(CommandHandler("start", start_nedhas))
    app_nedhas.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link_nedhas))
    app_nedhas.add_handler(CallbackQueryHandler(button_callback_nedhas, pattern=r"^(?!refresh_new_link).*$"))
    app_nedhas.add_handler(CallbackQueryHandler(refresh_callback_nedhas, pattern="^refresh_new_link$"))

    # বট ৪: Caption Bot
    app_caption.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND, handle_private_message_caption))
    app_caption.job_queue.run_repeating(post_caption_job, interval=1 * 60, first=10)

    print("🚀 ৪টি বট একসাথে চালু করার চেষ্টা করা হচ্ছে...")
    try:
        # --- এই অংশটুকু সম্পূর্ণ পরিবর্তন এবং সঠিক করা হয়েছে ---
        logger.info("Initializing all applications...")
        await asyncio.gather(*(app.initialize() for app in apps))

        logger.info("Starting all applications...")
        await asyncio.gather(*(app.start() for app in apps))
        
        updaters = [app.updater for app in apps if app.updater]
        logger.info("Starting all pollers...")
        await asyncio.gather(*(updater.start_polling() for updater in updaters))
        
        print("✅ ৪টি বট সফলভাবে চালু হয়েছে এবং চলছে...")
        await asyncio.Event().wait()

    finally:
        print("\n👋 বটগুলো বন্ধ করা হচ্ছে...")
        updaters_to_stop = [app.updater for app in apps if app.updater]
        if updaters_to_stop:
            await asyncio.gather(*(updater.stop() for updater in updaters_to_stop))
        await asyncio.gather(*(app.stop() for app in apps))
        await asyncio.gather(*(app.shutdown() for app in apps))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
