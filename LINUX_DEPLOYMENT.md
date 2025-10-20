# CameronPAD Linux Deployment Guide

This guide will help you deploy CameronPAD on a Linux server.

## Prerequisites

- Linux server (Ubuntu 20.04+, Debian 11+, or similar)
- Python 3.8 or higher
- Git (for cloning the repository)
- Sudo access (for installing system packages)

## Step 1: System Preparation

### Update system packages
```bash
sudo apt update
sudo apt upgrade -y
```

### Install Python and pip
```bash
sudo apt install -y python3 python3-pip python3-venv
```

### Install Git (if not already installed)
```bash
sudo apt install -y git
```

## Step 2: Clone the Repository

```bash
cd /opt  # or your preferred location
sudo git clone https://github.com/camayuki/cameronPAD.git
cd cameronPAD
```

Or if transferring files manually:
```bash
# On Windows (PowerShell), compress the project:
Compress-Archive -Path D:\Repositories\cameronPAD_main2\* -DestinationPath cameronpad.zip

# Transfer to Linux using scp, rsync, or FTP
# Then extract:
unzip cameronpad.zip -d /opt/cameronPAD
cd /opt/cameronPAD
```

## Step 3: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 5: Configure Environment

### Create environment file
```bash
cp .env.example .env
# Or create manually:
nano .env
```

### Minimum .env configuration
```env
# Environment
ENVIRONMENT=production

# Server
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-this-too

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/cameronpad.db

# Optional: Stock API Keys (for stocks plugin)
FINNHUB_TOKEN=your_finnhub_token_here
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here

# Optional: Surf API (for surf plugin)
STORMGLASS_API_KEY=your_stormglass_key_here
```

### Generate secure secret keys
```bash
# Generate random secret keys
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

## Step 6: Initialize Database

```bash
# Create data directory
mkdir -p data

# The database will be created automatically on first run
# But you can create an admin user:
python3 create_admin.py
```

## Step 7: Test the Application

```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Run the development server to test
python3 scripts/dev_server.py
```

Visit `http://your-server-ip:8000` to verify it works.

## Step 8: Production Deployment with Systemd

### Create systemd service file
```bash
sudo nano /etc/systemd/system/cameronpad.service
```

### Add the following content:
```ini
[Unit]
Description=CameronPAD Application
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/cameronPAD
Environment="PATH=/opt/cameronPAD/venv/bin"
EnvironmentFile=/opt/cameronPAD/.env
ExecStart=/opt/cameronPAD/venv/bin/python3 -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000 --workers 4

# Restart policy
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Set proper permissions
```bash
sudo chown -R www-data:www-data /opt/cameronPAD
sudo chmod -R 755 /opt/cameronPAD
```

### Enable and start the service
```bash
sudo systemctl daemon-reload
sudo systemctl enable cameronpad
sudo systemctl start cameronpad
```

### Check status
```bash
sudo systemctl status cameronpad
```

### View logs
```bash
sudo journalctl -u cameronpad -f
```

## Step 9: Configure Nginx Reverse Proxy (Recommended)

### Install Nginx
```bash
sudo apt install -y nginx
```

### Create Nginx configuration
```bash
sudo nano /etc/nginx/sites-available/cameronpad
```

### Add the following:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Change to your domain or IP

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    location /static {
        alias /opt/cameronPAD/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### Enable the site
```bash
sudo ln -s /etc/nginx/sites-available/cameronpad /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 10: SSL/HTTPS with Let's Encrypt (Optional but Recommended)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is set up automatically
```

## Step 11: Firewall Configuration

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

## Management Commands

### Restart the application
```bash
sudo systemctl restart cameronpad
```

### Stop the application
```bash
sudo systemctl stop cameronpad
```

### View logs
```bash
sudo journalctl -u cameronpad -f
```

### Update the application
```bash
cd /opt/cameronPAD
git pull  # or upload new files
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart cameronpad
```

## Backup

### Backup database and configuration
```bash
# Create backup directory
mkdir -p /opt/cameronPAD/backups

# Backup script
#!/bin/bash
BACKUP_DIR="/opt/cameronPAD/backups"
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "$BACKUP_DIR/cameronpad_backup_$DATE.tar.gz" \
    /opt/cameronPAD/data/ \
    /opt/cameronPAD/.env \
    /opt/cameronPAD/config/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "cameronpad_backup_*.tar.gz" -mtime +7 -delete
```

### Automate backups with cron
```bash
sudo crontab -e

# Add this line for daily backups at 2 AM:
0 2 * * * /opt/cameronPAD/backup.sh
```

## Troubleshooting

### Application won't start
```bash
# Check logs
sudo journalctl -u cameronpad -n 50

# Check permissions
ls -la /opt/cameronPAD

# Check Python dependencies
source /opt/cameronPAD/venv/bin/activate
pip list
```

### Database errors
```bash
# Check database file permissions
ls -la /opt/cameronPAD/data/

# Ensure data directory exists
mkdir -p /opt/cameronPAD/data
sudo chown www-data:www-data /opt/cameronPAD/data
```

### Port already in use
```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill the process if needed
sudo kill -9 <PID>
```

## Performance Tuning

### Increase worker processes
Edit `/etc/systemd/system/cameronpad.service`:
```ini
ExecStart=/opt/cameronPAD/venv/bin/python3 -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Workers = (2 × CPU cores) + 1

### Enable Nginx caching
Add to Nginx config:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=cameronpad_cache:10m max_size=100m inactive=60m;

location / {
    proxy_cache cameronpad_cache;
    proxy_cache_valid 200 60m;
    # ... other proxy settings
}
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Enable HTTPS with SSL certificate
- [ ] Configure firewall (ufw or iptables)
- [ ] Run as non-root user (www-data)
- [ ] Set proper file permissions (755 for directories, 644 for files)
- [ ] Keep system and Python packages updated
- [ ] Regular backups
- [ ] Monitor logs for suspicious activity

## Monitoring

### Install monitoring tools
```bash
# Install htop for system monitoring
sudo apt install -y htop

# Check system resources
htop

# Check disk usage
df -h

# Check memory usage
free -h
```

### Application health check
Create a simple monitoring script:
```bash
#!/bin/bash
curl -f http://localhost:8000/ || sudo systemctl restart cameronpad
```

Add to crontab to run every 5 minutes:
```bash
*/5 * * * * /opt/cameronPAD/healthcheck.sh
```

---

**Need help?** Check the logs first:
```bash
sudo journalctl -u cameronpad -f
```
