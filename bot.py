import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from instagrapi import Client

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
ALLOWED_CHANNEL_ID = os.getenv("ALLOWED_CHANNEL_ID")

SESSION_PATH = "session.json"
# Setup Instagram client
cl = Client()
if os.path.exists(SESSION_PATH):
    try:
        cl.load_settings(SESSION_PATH)
        cl.login(IG_USERNAME, IG_PASSWORD)
        print("✅ Loaded existing Instagram session")
    except Exception:
        print("⚠️ Session load failed, logging in fresh...")
        cl.login(IG_USERNAME, IG_PASSWORD)
else:
    cl.login(IG_USERNAME, IG_PASSWORD)
cl.dump_settings(SESSION_PATH)


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def handle_channel_post(update: Update, context: CallbackContext):
    post = update.channel_post
    
    if not post:
        return

    if ALLOWED_CHANNEL_ID:
        if str(post.chat.id) != str(ALLOWED_CHANNEL_ID):
            print(f"🚫 Unauthorized channel ID: {post.chat.id}")
            return
    else:
        print("⚠️ No channel restriction set. Please define ALLOWED_CHANNEL_ID.")
        return

    if not post.photo:
        return

    photo = post.photo[-1]
    caption = post.caption or ""
    file = context.bot.getFile(photo.file_id)
    path = f"{DOWNLOAD_DIR}/{photo.file_id}.jpg"
    file.download(custom_path=path)
    print(f"📥 Downloaded {path}")

    try:
        media = cl.photo_upload(path, caption)
        print(f"✅ Posted to Instagram: {media.pk}")
    except Exception as e:
        print(f"❌ Instagram upload failed: {e}")

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.update.channel_posts, handle_channel_post))

    print("🚀 Bot running — listening for new channel photos...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
