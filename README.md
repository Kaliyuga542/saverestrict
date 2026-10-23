# Telegram → GoFile uploader (authorized files)

This starter bot accepts a media file **sent directly to the bot**, downloads it to temporary storage, uploads it to GoFile, returns the link, and deletes the temporary copy.

It intentionally does **not** log into a Telegram user account, scrape private bot messages, or bypass protected-content / forwarding restrictions. Use it for files you own or are authorized to redistribute.

## Deploy to Koyeb

1. Create a Telegram bot with `@BotFather` and copy its token.
2. Push this folder to a GitHub repository.
3. In Koyeb, create a Worker service from the repository.
4. Build command: `pip install -r requirements.txt`
5. Run command: `python main.py`
6. Add environment variables:
   - `BOT_TOKEN` (required)
   - `GOFILE_TOKEN` (optional, if your GoFile account/API setup requires it)
   - `ALLOWED_USERS` (recommended: comma-separated Telegram numeric user IDs)
   - `MAX_FILE_MB` (default `1900`; set this below your host's memory/disk and Telegram limits)
7. Deploy and send a permitted test file to the bot.

## Important

- Check current Telegram Bot API file-size limits and GoFile API behavior before production use.
- Large files can exceed your hosting provider's temporary disk or request timeout limits.
- Never paste your bot token or Telegram login OTP/password into public repositories.
- `ALLOWED_USERS` left blank permits anyone who can find the bot to use it; set your own numeric user ID.
