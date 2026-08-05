# Vortex Telegram Bot — account linking for VortexSSH

Minimal bot process that accepts `/start <code>` and confirms the link
against Vortex Core (`POST /api/v1/internal/telegram/confirm`).

Core itself sends reminder messages via the Bot API (`TELEGRAM_BOT_TOKEN`).

## Setup

1. Create a bot with [@BotFather](https://t.me/BotFather), copy the token.
2. Set the same token on Core (`TELEGRAM_BOT_TOKEN`) and a shared secret
   (`TELEGRAM_BOT_API_KEY`) on both Core and this bot.
3. Set `TELEGRAM_BOT_USERNAME` on Core (without `@`) for deep links.

```bash
cp .env.example .env
# edit .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m bot
```

Docker:

```bash
docker compose up -d --build
```

## Link flow

1. User opens Vortex Web → Settings → Notifications → Link Telegram.
2. Core returns a one-time code + `https://t.me/<bot>?start=<code>`.
3. User opens the link; bot receives `/start <code>` and calls Core.
4. Core stores `telegram_chat_id` on the user.
