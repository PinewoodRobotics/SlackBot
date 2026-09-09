# Slack Bot - Simple Python Implementation

A dead-simple Slack bot built with Bolt for Python. No Docker, no complexity, just `python main.py`.

## Features

- **`/ping` slash command** → Responds with "Pong!"
- **"hello" message listener** → Detects "hello" (case-insensitive) and responds with "Hey there!"
- **`/add-all` slash command** → Adds all workspace members to the channel with confirmation
- **`-poll` auto-reactions** → Messages containing `-poll` get the same checkmark / x-mark reactions as the Quick Poll app. Skipped in `#transit`, `#announcements`, and `#food-orders` so those rooms are not double-reacted.

## Quick Start (Local Development)

Dependencies are managed with [uv](https://docs.astral.sh/uv/). Install it once with
`curl -LsSf https://astral.sh/uv/install.sh | sh` (or `brew install uv`).

```bash
# 1. Clone and setup
cd PWRUP_slack_bot
uv sync          # creates .venv, installs the locked dependencies

# 2. Configure environment
cp .env.example .env
# Edit .env with your Slack tokens (see Setup Guide below)

# 3. Run the bot
uv run main.py
```

Useful uv commands:

```bash
uv add <package>        # add a dependency (updates pyproject.toml + uv.lock)
uv remove <package>     # drop a dependency
uv lock --upgrade       # refresh the lockfile to the latest allowed versions
uv sync --locked        # install exactly what uv.lock specifies (use in CI/deploy)
```

---

## 📋 Complete Setup Guide

### Step 1: Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name it (e.g., "PWRUP Bot") and select your workspace
4. Click **"Create App"**

### Step 2: Configure Bot Permissions

1. In your app settings, go to **"OAuth & Permissions"**
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Add these scopes:
   - `chat:write` - Send messages
   - `commands` - Use slash commands
   - `channels:history` - Read messages in public channels
   - `groups:history` - Read messages in private channels
   - `im:history` - Read direct messages
   - `mpim:history` - Read group messages
   - `users:read` - List workspace members
   - `channels:read` - Read channel info
   - `channels:manage` - Invite users to channels
   - `groups:write` - Invite users to private channels
   - `reactions:write` - Seed `-poll` checkmark / x-mark reactions

4. Scroll up and click **"Install to Workspace"**
5. Authorize the app
6. **Copy the "Bot User OAuth Token"** (starts with `xoxb-`)
   - Save this as `SLACK_BOT_TOKEN` in your `.env` file

### Step 3: Get Signing Secret

1. Go to **"Basic Information"** in your app settings
2. Scroll to **"App Credentials"**
3. **Copy the "Signing Secret"**
   - Save this as `SLACK_SIGNING_SECRET` in your `.env` file

### Step 4: Create Slash Commands

1. Go to **"Slash Commands"** in your app settings
2. Click **"Create New Command"** for `/ping`:
   - **Command:** `/ping`
   - **Request URL:** `https://your-domain.com/slack/events`
   - **Short Description:** "Ping the bot"
3. Click **"Create New Command"** for `/add-all`:
   - **Command:** `/add-all`
   - **Request URL:** `https://your-domain.com/slack/events`
   - **Short Description:** "Add all workspace members to this channel"

### Step 5: Enable Event Subscriptions

1. Go to **"Event Subscriptions"** in your app settings
2. Toggle **"Enable Events"** to ON
3. **Request URL:** `https://your-domain.com/slack/events`
   - ⚠️ You need to deploy your bot first before Slack can verify this URL
4. Scroll to **"Subscribe to bot events"**
5. Add these events:
   - `message.channels` - Messages in public channels
   - `message.groups` - Messages in private channels
   - `message.im` - Direct messages
   - `message.mpim` - Group messages
6. Click **"Save Changes"**

---

## 🚀 Production Deployment (Coolify)

The bot runs at **https://slack.pinewoodrobotics.org** on the Coolify instance at
`coolify.techclub.pw`, built from the `Dockerfile` in this repo and served by
gunicorn via `wsgi.py`. Slack reaches it over HTTP at `/slack/events`; Socket Mode
is not used in production.

**Pushing to `main` deploys.** A GitHub push webhook notifies Coolify, which
rebuilds and restarts the container. To deploy without pushing:

```bash
coolify deploy uuid kckbia9skc8pzyz1vv3vvccr --force
coolify app deployments logs kckbia9skc8pzyz1vv3vvccr --follow
coolify app logs kckbia9skc8pzyz1vv3vvccr --follow
```

Environment variables live in Coolify, not in a `.env` file. `SLACK_APP_TOKEN` is
deliberately unset — setting it would flip the bot into Socket Mode.

`GET /health` returns `{"status":"ok"}` and is what the container healthcheck probes.

---

## 🚀 Ubuntu Server Deployment (legacy)

The systemd + Cloudflare Tunnel setup below predates the Coolify deployment and is
kept for reference.

### Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install curl, then uv (uv provides the pinned Python itself)
sudo apt install curl -y
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

### Deployment Steps

#### 1. Upload Your Code

```bash
# On your Ubuntu server
cd /opt
sudo git clone https://github.com/PinewoodRobotics/SlackBot.git
cd SlackBot

# Or upload files manually with scp:
# scp -r /path/to/PWRUP_slack_bot user@your-server:/opt/SlackBot
```

#### 2. Setup Python Environment

```bash
cd /opt/SlackBot
sudo chown -R $USER:$USER .
uv sync --locked
```

#### 3. Configure Environment

```bash
# Create .env file
cp .env.example .env
nano .env

# Add your tokens:
# SLACK_BOT_TOKEN=xoxb-your-actual-token
# SLACK_SIGNING_SECRET=your-actual-secret
# PORT=3000
```

#### 4. Test the Bot

```bash
# Run manually to test
python main.py

# You should see: ⚡️ Slack bot is starting on port 3000...
# Press Ctrl+C to stop
```

#### 5. Setup Systemd Service (Run on Bot)

```bash
# Create service file
sudo nano /etc/systemd/system/slackbot.service
```

Paste this content:

```ini
[Unit]
Description=PWRUP Slack Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/SlackBot
Environment="PATH=/opt/SlackBot/.venv/bin"
EnvironmentFile=/opt/SlackBot/.env
ExecStart=/opt/SlackBot/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Note:** Change `User=ubuntu` to your actual username if different.

```bash
# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable slackbot
sudo systemctl start slackbot

# Check status
sudo systemctl status slackbot

# View logs
sudo journalctl -u slackbot -f
```

#### 6. Setup Cloudflare Tunnel

```bash
# Install Cloudflare Tunnel
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
rm cloudflared.deb

# Authenticate with Cloudflare
cloudflared tunnel login

# Create a tunnel (replace 'slackbot' with your preferred name)
cloudflared tunnel create slackbot

# Get your tunnel ID from the output
```

Create config file at `~/.cloudflared/config.yml`:

```yaml
tunnel: slackbot
credentials-file: ~/.cloudflared/<YOUR-TUNNEL-ID>.json

ingress:
  - hostname: your-domain.com
    service: http://localhost:3000
  - service: http_status:404
```

Create systemd service for tunnel:

```bash
sudo nano /etc/systemd/system/cloudflared.service
```

```ini
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=ubuntu
ExecStart=/usr/local/bin/cloudflared tunnel --config ~/.cloudflared/config.yml run slackbot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
sudo systemctl status cloudflared
```

#### 7. Update Slack App URLs

Now go back to your Slack app settings:

1. **Event Subscriptions** → Request URL: `https://your-domain.com/slack/events`
2. **Slash Commands** → `/ping` → Request URL: `https://your-domain.com/slack/events`
3. Click **"Save Changes"**

Slack will verify the URL (should show a green checkmark ✓)

---

## 🧪 Testing

### Test `/ping` Command

In any Slack channel where the bot is added:
```
/ping
```
Expected response: `Pong!`

### Test Message Listener

In any channel where the bot is added:
```
hello
Hello
HELLO
hey hello there
```
Expected response: `Hey there <@your_username>!`

### Test `/add-all` Command

In any channel where the bot is added:
```
/add-all
```
Expected: Ephemeral message (only visible to you) showing all members to be added with Confirm/Cancel buttons. Click Confirm to add them all.

### Test `-poll` auto-reactions

In any channel **except** `#transit`, `#announcements`, and `#food-orders` (Quick Poll already seeds those):

```
test -poll
```

Expected: the bot adds `:sf-symbols_checkmark-square-fill:` then `:sf-symbols_xmark-square-fill:` to the message.

In those three excluded channels the bot must add nothing. Requires the Slack app to have the `reactions:write` bot scope (add it under OAuth & Permissions in the Slack app UI; this repo cannot grant it).

Unit tests for the trigger / exclusion logic:

```
uv run python -m unittest tests.test_poll
```

---

## 🔧 Useful Commands

```bash
# View bot logs
sudo journalctl -u slackbot -f

# Restart bot
sudo systemctl restart slackbot

# Stop bot
sudo systemctl stop slackbot

# Check bot status
sudo systemctl status slackbot

# Update code and restart
cd /opt/SlackBot
git pull
sudo systemctl restart slackbot
```

---

## 🐛 Troubleshooting

### Bot not responding to /ping

1. Check if service is running: `sudo systemctl status slackbot`
2. Check logs: `sudo journalctl -u slackbot -f`
3. Verify Slack slash command URL is correct
4. Make sure bot is installed in your workspace

### Bot not responding to "hello"

1. Make sure bot is **invited to the channel**: `/invite @YourBotName`
2. Check Event Subscriptions are enabled
3. Verify bot has correct scopes (see Step 2)
4. Check logs for errors

### "url_verification failed" error

- This happens when Slack can't verify your URL
- Make sure bot is running: `sudo systemctl status slackbot`
- Make sure tunnel is running: `sudo systemctl status cloudflared`
- Verify tunnel is connected: `sudo journalctl -u cloudflared -f`
- Check bot is responding: `curl https://your-domain.com/slack/events`

### Port 3000 already in use

```bash
# Find what's using port 3000
sudo lsof -i :3000

# Kill the process or change PORT in .env
```

### Cloudflare Tunnel issues

```bash
# Check tunnel status
sudo systemctl status cloudflared

# View tunnel logs
sudo journalctl -u cloudflared -f

# Restart tunnel
sudo systemctl restart cloudflared

# List active tunnels
cloudflared tunnel list
```

---

## 📁 Project Structure

```
PWRUP_slack_bot/
├── main.py              # Entrypoint: builds the app, registers handlers, starts it
├── config.py            # Environment configuration
├── commands/            # Slash commands
│   ├── ping.py          # /ping
│   └── add_all.py       # /add-all plus its Confirm/Cancel buttons
├── events/              # Event subscriptions
│   ├── channels.py      # channel_created -> auto-join
│   ├── mentions.py      # app_mention -> greeting
│   └── poll.py          # message containing -poll -> seed reactions
├── tests/
│   └── test_poll.py     # -poll trigger, exclusions, reaction seeding
├── utils/
│   ├── slack.py         # Shared Slack API helpers
│   └── autojoin.py      # Background join-all-public-channels on startup
├── pyproject.toml       # Project metadata + dependencies (uv)
├── uv.lock              # Pinned dependency versions (commit this)
├── .python-version      # Pinned Python version (3.12)
├── .env.example        # Environment template
├── .env                # Your actual config (git-ignored)
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

---

## 🔐 Security Notes

- Never commit `.env` to git (it's in `.gitignore`)
- Keep your tokens secret
- Use HTTPS in production (handled by certbot)
- Slack automatically verifies requests using the signing secret

---

## 📚 Resources

- [Slack Bolt Python Docs](https://slack.dev/bolt-python/)
- [Slack API Documentation](https://api.slack.com/)
- [Slack App Management](https://api.slack.com/apps)

---

## 🎉 That's It!

You now have a production-ready Slack bot running on your Ubuntu server. No Docker, no complexity, just Python.

**Questions?** Check the logs: `sudo journalctl -u slackbot -f`

