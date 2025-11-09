import os, time
from collections import defaultdict
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

media_groups = defaultdict(list)
group_timestamps = {}

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

    caption = post.caption or ""

    # Skip rule: messages starting with "=skip"
    if caption.strip().lower().startswith("=skip"):
        print("⚠️ Skipping post (marked with =skip)")
        return

    if not post.photo and not post.video:
        return

    photo = post.photo[-1]
    file = context.bot.getFile(photo.file_id)
    path = f"{DOWNLOAD_DIR}/{photo.file_id}.jpg"
    file.download(custom_path=path)
    print(f"📥 Downloaded {path}")

    if post.media_group_id:
        gid = post.media_group_id
        media_groups[gid].append(path)
        group_timestamps[gid] = time.time()
        print(f"🧩 Added photo to group {gid}")
    else:
        # Single image post
        upload_to_instagram([path], caption)


def upload_to_instagram(paths, caption):
    try:
        if len(paths) > 1:
            cl.album_upload(paths, caption=caption)
            print(f"✅ Uploaded album with {len(paths)} images.")
        else:
            cl.photo_upload(paths[0], caption=caption, alt_text=caption)
            print("✅ Uploaded single photo.")
    except Exception as e:
        print(f"❌ Instagram upload failed: {e}")
    finally:
        for p in paths:
            if os.path.exists(p):
                os.remove(p)

def check_media_groups(context: CallbackContext):
    now = time.time()
    expired = [gid for gid, t in group_timestamps.items() if now - t > 5]

    for gid in expired:
        paths = media_groups.pop(gid, [])
        group_timestamps.pop(gid, None)
        if paths:
            print(f"📦 Uploading album for group {gid} ({len(paths)} photos)")
            # Use caption from the first photo (can adjust logic)
            caption = "#sketch"
            upload_to_instagram(paths, caption)

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.update.channel_posts, handle_channel_post))

    job_queue = updater.job_queue
    job_queue.run_repeating(check_media_groups, interval=3, first=5)

    print("🚀 Bot running — listening for new channel photos...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
