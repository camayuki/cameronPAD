# CameronPAD Deployment Guide

## Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git (optional, for cloning repository)

## Quick Start (Linux/Unix)

### 1. Clone or Transfer Repository
```bash
# Option A: Clone from git
git clone <your-repo-url> cameronpad
cd cameronpad

# Option B: Transfer files via scp
scp -r /path/to/cameronpad user@server:/home/user/
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
# Copy example .env file (if provided) or create new one
cat > .env << 'EOF'
# Stock Service API Keys
FINNHUB_TOKEN=your_finnhub_token_here
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here

# Service Configuration
POLL_SECONDS=60
SHOWCASE_REFRESH=300
COOLDOWN_MIN=30
ALPHA_MIN_INTERVAL=13.0

# Application Configuration (optional)
SECRET_KEY=your-secret-key-here-change-this-in-production
DEBUG=false
EOF

# Update with your actual API keys
nano .env  # or use vim, vi, etc.
```

### 5. Initialize Database
```bash
# The database will be created automatically on first run
# But you need to create an admin user
python create_admin.py
```

### 6. Run the Application

#### Development Mode
```bash
# With auto-reload (for testing)
python -m uvicorn app_new.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode (Basic)
```bash
# Single worker
python -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000
```

#### Production Mode (Recommended - with Gunicorn)
```bash
# Install gunicorn first
pip install gunicorn

# Run with multiple workers
gunicorn app_new.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### 7. Access the Application
Open your browser and navigate to:
```
http://your-server-ip:8000
```

## Running as a System Service (systemd)

### Create Service File
```bash
sudo nano /etc/systemd/system/cameronpad.service
```

### Service Configuration
```ini
[Unit]
Description=CameronPAD Application
After=network.target

[Service]
Type=notify
User=your-username
Group=your-username
WorkingDirectory=/home/your-username/cameronpad
Environment="PATH=/home/your-username/cameronpad/venv/bin"
ExecStart=/home/your-username/cameronpad/venv/bin/gunicorn app_new.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable cameronpad

# Start the service
sudo systemctl start cameronpad

# Check status
sudo systemctl status cameronpad

# View logs
sudo journalctl -u cameronpad -f
```

## Nginx Reverse Proxy (Optional but Recommended)

### Install Nginx
```bash
sudo apt update
sudo apt install nginx
```

### Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/cameronpad
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;  # or your server IP

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # WebSocket support (if needed in future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /home/your-username/cameronpad/static;
        expires 30d;
    }
}
```

### Enable Nginx Site
```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/cameronpad /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

## Firewall Configuration

```bash
# Allow HTTP traffic
sudo ufw allow 80/tcp

# Allow HTTPS traffic (if using SSL)
sudo ufw allow 443/tcp

# If accessing directly without Nginx
sudo ufw allow 8000/tcp
```

## SSL/HTTPS Setup with Let's Encrypt (Optional)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Certificates will auto-renew
```

## Troubleshooting

### Check Application Logs
```bash
# If running with systemd
sudo journalctl -u cameronpad -n 100 --no-pager

# If running manually, logs go to stdout/stderr
```

### Check if Port is in Use
```bash
sudo netstat -tulpn | grep :8000
```

### Test Application Directly
```bash
# Activate venv
source venv/bin/activate

# Run in foreground to see errors
python -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000
```

### Verify Environment Variables Loaded
```bash
# In Python
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Finnhub:', os.getenv('FINNHUB_TOKEN'))"
```

### Database Issues
```bash
# Check database file exists
ls -la data/

# Run database check script
python check_db.py
```

### Permission Issues
```bash
# Ensure proper ownership
sudo chown -R your-username:your-username /home/your-username/cameronpad

# Ensure data directory is writable
chmod 755 data/
```

## Updating the Application

```bash
# Pull latest changes (if using git)
git pull

# Activate venv
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart cameronpad
```

## Backup Recommendations

### Database Backup
```bash
# Create backup directory
mkdir -p ~/backups

# Backup database
cp data/cameronpad_dev.db ~/backups/cameronpad_$(date +%Y%m%d_%H%M%S).db

# Automated daily backup (add to crontab)
0 2 * * * cp /home/your-username/cameronpad/data/cameronpad_dev.db /home/your-username/backups/cameronpad_$(date +\%Y\%m\%d).db
```

## Monitoring

### Check Application Health
```bash
# Simple health check
curl http://localhost:8000/

# Check API status
curl http://localhost:8000/api/v1/plugins/stocks/service-status
```

### Monitor Resource Usage
```bash
# Check memory and CPU
htop

# Check disk space
df -h

# Monitor specific process
ps aux | grep uvicorn
```

## Security Best Practices

1. **Change Default Secrets**: Update `SECRET_KEY` in `.env`
2. **Use Strong Passwords**: When creating admin user
3. **Keep Dependencies Updated**: Regularly run `pip install -r requirements.txt --upgrade`
4. **Use HTTPS**: Set up SSL certificate with Let's Encrypt
5. **Firewall Rules**: Only open necessary ports
6. **Regular Backups**: Automate database backups
7. **Monitor Logs**: Check logs regularly for suspicious activity

## Performance Tuning

### Gunicorn Workers
```bash
# Rule of thumb: (2 x CPU cores) + 1
# For 2 CPU cores:
--workers 5

# For 4 CPU cores:
--workers 9
```

### Database Optimization
```bash
# If database gets large, consider vacuum
sqlite3 data/cameronpad_dev.db "VACUUM;"
```

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u cameronpad -f`
2. Review DEBUGGING_GUIDE.md (if available)
3. Verify all environment variables are set correctly
4. Ensure all dependencies are installed: `pip list`
