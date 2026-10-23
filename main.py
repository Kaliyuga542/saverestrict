import os
import tempfile
import logging
from pathlib import Path

import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO"),
)
log = logging.getLogger("tg-gofile")

BOT_TOKEN = os.environ["BOT_TOKEN"]
GOFILE_TOKEN = os.getenv("GOFILE_TOKEN", "").strip()
MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "1900"))
ALLOWED_USERS = {
    int(x.strip()) for x in os.getenv("ALLOWED_USERS", "").split(",")
    if x.strip().isdigit()
}

def allowed(update: Update) -> bool:
    user = update.effective_user
    return bool(user and (not ALLOWED_USERS or user.id in ALLOWED_USERS))

def upload_to_gofile(path: str) -> str:
    # GoFile API: obtain an upload server, then upload the file.
    headers = {}
    if GOFILE_TOKEN:
        headers["Authorization"] = f"Bearer {GOFILE_TOKEN}"

    r = requests.get("https://api.gofile.io/servers", timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "ok" or not data.get("data", {}).get("servers"):
        raise RuntimeError(f"GoFile server lookup failed: {data}")
    server = data["data"]["servers"][0]["name"]
    endpoint = f"https://{server}.gofile.io/contents/upload"

    with open(path, "rb") as f:
        response = requests.post(
            endpoint,
            headers=headers,
            files={"file": (Path(path).name, f, "application/octet-stream")},
            data={"folderId": ""},
            timeout=(30, 3600),
        )
    response.raise_for_status()
    result = response.json()
    if result.get("status") != "ok":
        raise RuntimeError(f"GoFile upload failed: {result}")
    payload = result.get("data", {})
    return payload.get("downloadPage") or payload.get("url") or ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return
    await update.message.reply_text(
        "Send me a video/document that you own or have permission to share. "
        "I'll upload it to GoFile and return the link. "
        "This bot does not fetch protected Telegram posts or bypass forwarding restrictions."
    )

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    message = update.effective_message
    media = message.document or message.video or message.audio
    if not media:
        await message.reply_text("Please send a video, audio, or document file.")
        return

    size = getattr(media, "file_size", None) or 0
    if size and size > MAX_FILE_MB * 1024 * 1024:
        await message.reply_text(f"File is too large. Limit: {MAX_FILE_MB} MB.")
        return

    original_name = getattr(media, "file_name", None)
    if not original_name:
        original_name = f"telegram_file_{media.file_unique_id}.bin"
    status = await message.reply_text("⬇️ Downloading file…")
    tmp_path = None
    try:
        tg_file = await context.bot.get_file(media.file_id)
        suffix = Path(original_name).suffix[:20]
        with tempfile.NamedTemporaryFile(prefix="tg_", suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
        await tg_file.download_to_drive(custom_path=tmp_path)

        await status.edit_text("⬆️ Uploading to GoFile…")
        link = upload_to_gofile(tmp_path)
        if not link:
            raise RuntimeError("GoFile returned no download link.")
        await status.edit_text(f"✅ Upload complete\n\n📁 `{original_name}`\n🔗 {link}", parse_mode="Markdown")
    except Exception as exc:
        log.exception("Media upload failed")
        await status.edit_text(f"❌ Upload failed: {str(exc)[:700]}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                log.warning("Could not delete temporary file: %s", tmp_path)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if allowed(update):
        await update.message.reply_text(
            "Usage:\n1) Send a file directly to this bot.\n"
            "2) Wait for download and GoFile upload.\n"
            "3) Receive the GoFile link.\n\n"
            "For privacy, set ALLOWED_USERS to your Telegram numeric user ID."
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.VIDEO | filters.AUDIO, handle_media))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
