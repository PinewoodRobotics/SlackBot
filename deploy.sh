#!/bin/bash
# Quick deployment script for Ubuntu server with Cloudflare Tunnel
# Run this on your Ubuntu server after uploading the code

set -e  # Exit on error

echo "🚀 PWRUP Slack Bot Deployment Script"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run as root. Run as your normal user."
    exit 1
fi

# Get current directory
INSTALL_DIR=$(pwd)
echo "📁 Installing in: $INSTALL_DIR"
echo ""

# Step 1: Install system dependencies
echo "📦 Step 1: Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv curl

# Step 2: Install Cloudflare Tunnel
echo ""
echo "🌐 Step 2: Installing Cloudflare Tunnel..."
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
rm cloudflared.deb
echo "✅ Cloudflare Tunnel installed"

# Step 3: Setup Python virtual environment
echo ""
echo "🐍 Step 3: Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Setup environment file
echo ""
echo "⚙️  Step 4: Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: You need to edit .env with your Slack tokens!"
    echo "   Run: nano .env"
    echo "   Add your SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET"
    echo ""
    read -p "Press Enter after you've edited .env..."
else
    echo "✅ .env file already exists"
fi

# Step 5: Test the bot
echo ""
echo "🧪 Step 5: Testing the bot..."
echo "Starting bot for 5 seconds to test..."
timeout 5 python main.py || true
echo "✅ Bot test complete"

# Step 6: Setup systemd service for bot
echo ""
echo "🔧 Step 6: Setting up systemd service for bot..."
SERVICE_FILE="/etc/systemd/system/slackbot.service"

sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=PWRUP Slack Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Created systemd service file"

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable slackbot
sudo systemctl start slackbot

echo "✅ Service started"
echo ""
echo "📊 Service status:"
sudo systemctl status slackbot --no-pager

# Step 7: Setup Cloudflare Tunnel
echo ""
echo "🌐 Step 7: Setting up Cloudflare Tunnel..."
echo ""
echo "You need to authenticate with Cloudflare."
echo "This will open a browser to log in. If you're on a headless server,"
echo "copy the URL and open it on your local machine."
echo ""
read -p "Press Enter to continue..."

cloudflared tunnel login

echo ""
echo "Enter a name for your tunnel (e.g., slackbot):"
read TUNNEL_NAME

if [ -z "$TUNNEL_NAME" ]; then
    TUNNEL_NAME="slackbot"
fi

# Create tunnel
TUNNEL_ID=$(cloudflared tunnel create $TUNNEL_NAME 2>&1 | grep -oP 'Tunnel ID: \K[a-f0-9-]+' || echo "")

if [ -z "$TUNNEL_ID" ]; then
    echo "⚠️  Tunnel creation may have failed. Check the output above."
    echo "You can manually create a tunnel with: cloudflared tunnel create $TUNNEL_NAME"
    read -p "Press Enter to continue..."
fi

# Create config file
CONFIG_DIR="$HOME/.cloudflared"
mkdir -p $CONFIG_DIR

echo ""
echo "Enter your domain (e.g., bot.example.com):"
read DOMAIN

if [ -z "$DOMAIN" ]; then
    echo "❌ Domain is required"
    exit 1
fi

# Create config
sudo tee /etc/systemd/system/cloudflared.service > /dev/null <<EOF
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/usr/local/bin/cloudflared tunnel --config $CONFIG_DIR/config.yml run $TUNNEL_NAME
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create tunnel config
tee $CONFIG_DIR/config.yml > /dev/null <<EOF
tunnel: $TUNNEL_NAME
credentials-file: $CONFIG_DIR/$TUNNEL_ID.json

ingress:
  - hostname: $DOMAIN
    service: http://localhost:3000
  - service: http_status:404
EOF

echo "✅ Cloudflare Tunnel configured"

# Enable and start tunnel
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

echo "✅ Tunnel started"
echo ""
echo "📊 Tunnel status:"
sudo systemctl status cloudflared --no-pager

# Final steps
echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "📝 Next steps:"
echo "1. Go to https://api.slack.com/apps → Your App"
echo "2. Set Event Subscriptions URL to: https://$DOMAIN/slack/events"
echo "3. Set Slash Command URL to: https://$DOMAIN/slack/events"
echo "4. Test your bot with /ping in Slack"
echo ""
echo "🔧 Useful commands:"
echo "  View bot logs:     sudo journalctl -u slackbot -f"
echo "  View tunnel logs:  sudo journalctl -u cloudflared -f"
echo "  Restart bot:       sudo systemctl restart slackbot"
echo "  Restart tunnel:    sudo systemctl restart cloudflared"
echo ""
echo "🎉 Happy Slacking!"

