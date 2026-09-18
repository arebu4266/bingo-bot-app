# Hager Bingo - Telegram Mini App

A Telegram **Mini App** (Web App) version of the bingo bot: a real full-screen
game board like MeriBingo / DIL Bingo, backed by a small FastAPI server.

## Project structure
```
hager_bingo/
├── app.py              # FastAPI backend + Telegram webhook + game API
├── bingo_logic.py       # Card generation / win checking
├── db.py                # SQLite wallet
├── static/index.html    # The Mini App UI (what users see inside Telegram)
├── requirements.txt
├── .env.example
└── .gitignore
```

## How it works
- One shared "room" is running at all times. When the first player joins,
  a 20 second countdown starts; when it ends, the game begins and numbers
  are called automatically every few seconds.
- The Mini App page polls `/api/state` every 2 seconds to stay in sync with
  everyone else - no need to install anything else for real-time behavior
  at this scale.
- Wallet balance is per Telegram user ID, verified using Telegram's
  official WebApp `initData` signature check (see `verify_init_data` in
  `app.py`) - a user cannot spend or claim prizes for another user's ID.
- `/api/deposit` is still a **demo stub** - wire it to your licensed payment
  provider (Telebirr, CBE Birr, etc.) before handling real money. Only
  credit a balance after the provider confirms the payment server-side.

## Deploy for free on Render.com

1. **Push this folder to a GitHub repo** (private repo recommended, since
   this handles money logic):
   ```bash
   git init
   git add .
   git commit -m "Hager Bingo mini app"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Create a Render account** at https://render.com (free tier is enough
   to start).

3. **New + → Web Service** → connect your GitHub repo.

4. Configure the service:
   - **Runtime**: Python 3
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance type**: Free

5. **Environment variables** (Render dashboard → Environment):
   - `BOT_TOKEN` = your bot token from @BotFather (revoke and use a fresh
     one - never reuse a token that was ever shared elsewhere)
   - `WEBAPP_URL` = the `https://your-app-name.onrender.com` URL Render
     gives you after the first deploy (you'll need to redeploy once you
     know this URL - see step 7)
   - `CARD_PRICE`, `NUMBER_CALL_INTERVAL`, `COMMISSION` = optional, see
     `.env.example` for defaults

6. Click **Deploy**. Wait for the build to finish and note the URL Render
   assigns you, e.g. `https://hager-bingo.onrender.com`.

7. **Set `WEBAPP_URL`** to that exact URL in the environment variables (if
   you hadn't already), then **manually redeploy** so the bot registers
   its webhook with the correct URL.

8. Open Telegram, find your bot, send `/start` - you should see a
   **"Play Hager Bingo"** button that opens the Mini App full-screen.

### About the free tier
Render's free web services **spin down after ~15 minutes of inactivity**
and take 30-60 seconds to wake up on the next request. That's fine for
testing and low-traffic launches. Once you have real users and money
moving through it, upgrade to a paid instance (or a small VPS) so the
game doesn't go to sleep mid-round.

## Local testing (optional, before deploying)
```bash
pip install -r requirements.txt
cp .env.example .env   # fill in BOT_TOKEN; leave WEBAPP_URL blank for now
uvicorn app:app --reload
```
Without `WEBAPP_URL` set, `/start` will reply with a plain text message
instead of the Play button (Telegram requires a real HTTPS URL for
`web_app` buttons - `localhost` won't work). Use Render (or a tunnel tool
someone on your team is comfortable with) to get an HTTPS URL for testing
the button itself.

## Before accepting real money
- Get your **payment provider integration** done and tested (see
  `/api/deposit` and add a matching withdrawal endpoint).
- Add logging/monitoring so failed payments or crashes are visible.
- Consider moving from SQLite to Postgres if you expect concurrent load
  (Render offers a free Postgres tier too).
- Have your gambling license paperwork and terms of service linked
  somewhere in the Mini App.
