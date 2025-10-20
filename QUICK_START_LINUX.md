# 🚀 Quick Start for Linux

This guide will help you get CameronPAD running on your Linux server in minutes.

## Prerequisites

- Linux server (Ubuntu 20.04+, Debian 11+, CentOS 8+, or similar)
- Python 3.8 or higher
- 1GB RAM minimum (2GB recommended)
- 1GB disk space minimum

## Quick Installation

### 1. Install Python 3.8+ (if not installed)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3 python3-pip
```

### 2. Transfer Files to Linux

**Option A: Using Git (recommended)**
```bash
git clone https://github.com/camayuki/cameronPAD.git
cd cameronPAD
```

**Option B: Manual Transfer**
```bash
# On Windows, compress the folder
# Then use SCP, SFTP, or your preferred method to transfer

# On Linux, extract:
unzip cameronpad.zip
cd cameronPAD
```

### 3. Run Setup Script

```bash
chmod +x setup_linux.sh
./setup_linux.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Generate secure secret keys
- Create necessary directories
- Make scripts executable

### 4. Create Admin User

```bash
source venv/bin/activate
python3 create_admin.py
```

Follow the prompts to create your admin account.

### 5. Start the Application

**Development mode (with auto-reload):**
```bash
./start.sh
```

**Production mode (multiple workers):**
```bash
./start_prod.sh
```

### 6. Access the Application

Open your browser and navigate to:
```
http://your-server-ip:8000
```

Default login:
- Username: (the one you created)
- Password: (the one you created)

## 🎯 That's it!

You now have CameronPAD running on your Linux server.

## Next Steps

### For Production Deployment

1. **Set up as a system service:**
   See [LINUX_DEPLOYMENT.md](LINUX_DEPLOYMENT.md) for detailed systemd setup

2. **Configure Nginx reverse proxy:**
   ```bash
   sudo apt install nginx
   # See LINUX_DEPLOYMENT.md for configuration
   ```

3. **Enable SSL/HTTPS:**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

4. **Configure firewall:**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

## 🔧 Configuration

### Environment Variables

Edit `.env` file to customize:

```bash
nano .env
```

Important settings:
- `SECRET_KEY` - Change for production!
- `JWT_SECRET_KEY` - Change for production!
- `ENVIRONMENT` - Set to `production` for production
- `HOST` - 0.0.0.0 to listen on all interfaces
- `PORT` - Default 8000

### API Keys (Optional)

For full functionality, add these to `.env`:

**Stock Plugin:**
- `FINNHUB_TOKEN` - Get from https://finnhub.io/
- `ALPHA_VANTAGE_KEY` - Get from https://www.alphavantage.co/

**Surf Plugin:**
- `STORMGLASS_API_KEY` - Get from https://stormglass.io/

## 📊 Management

### View Logs

If running in terminal:
```bash
# Logs are displayed in the terminal
```

If running as systemd service:
```bash
sudo journalctl -u cameronpad -f
```

### Restart Application

If running in terminal:
```bash
# Press Ctrl+C to stop
./start.sh  # or ./start_prod.sh
```

If running as systemd service:
```bash
sudo systemctl restart cameronpad
```

### Stop Application

If running in terminal:
```bash
# Press Ctrl+C
```

If running as systemd service:
```bash
sudo systemctl stop cameronpad
```

### Update Application

```bash
cd /path/to/cameronPAD
git pull  # or upload new files
source venv/bin/activate
pip install -r requirements.txt
# Restart the application
```

## 🆘 Troubleshooting

### Port already in use

```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>
```

### Permission denied

```bash
# Make scripts executable
chmod +x *.sh

# Fix data directory permissions
chmod 755 data/
```

### Python version too old

```bash
# Check Python version
python3 --version

# If < 3.8, install newer version:
# Ubuntu 20.04+
sudo apt install python3.10 python3.10-venv
```

### Dependencies won't install

```bash
# Update pip
pip install --upgrade pip

# Install build essentials (may be needed for some packages)
sudo apt install build-essential python3-dev
```

### Can't access from other computers

```bash
# Make sure you're binding to 0.0.0.0
# Check .env file:
HOST=0.0.0.0

# Check firewall
sudo ufw allow 8000/tcp
```

## 📚 Documentation

- **[LINUX_DEPLOYMENT.md](LINUX_DEPLOYMENT.md)** - Complete production deployment guide
- **[README.md](README.md)** - Main project documentation
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - All available documentation

## 🔐 Security

**Important for production:**

1. Change SECRET_KEY and JWT_SECRET_KEY in `.env`
2. Use HTTPS (SSL certificate)
3. Configure firewall
4. Run as non-root user
5. Keep system updated
6. Regular backups

## 💾 Backup

Quick backup command:
```bash
tar -czf cameronpad_backup_$(date +%Y%m%d).tar.gz data/ .env config/
```

Restore:
```bash
tar -xzf cameronpad_backup_YYYYMMDD.tar.gz
```

## 🌟 Features

- **Multi-user** - User and group management with admin panel
- **Notes** - Shared and private notes with group permissions
- **Stocks** - Real-time stock tracking with alerts
- **Journal** - Personal daily journal
- **Surf** - Surf conditions monitoring
- **Themes** - 100+ themes available from marketplace
- **System Monitor** - Server resource monitoring
- **Notepad** - Multi-tab text editor
- **TradingView** - Embedded charts

## 📞 Support

If you encounter issues:

1. Check logs: `sudo journalctl -u cameronpad -f`
2. Check system resources: `htop`
3. Check disk space: `df -h`
4. Verify Python version: `python3 --version`
5. Check dependencies: `pip list`

## 📄 License

[Your License Here]

## 🙏 Credits

Built with FastAPI, SQLite, and ❤️
