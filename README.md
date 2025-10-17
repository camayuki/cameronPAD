# CameronPAD

A modular web application platform with plugin support for various tools and services.

## Features

- 📊 **Stock Monitoring**: Real-time stock price tracking with Finnhub and Alpha Vantage APIs
- 📝 **Notes & Notepad**: Quick note-taking capabilities
- 📔 **Journal**: Daily journaling with file uploads
- 🏄 **Surf Tracker**: Custom surf condition monitoring
- 🖥️ **System Monitor**: Server resource monitoring (CPU, Memory, Disk)
- 📈 **TradingView Integration**: Embedded charts and analysis
- 🔌 **Plugin System**: Easily extend with custom plugins

## Quick Start

### Windows
```powershell
# Run the setup script
.\setup.ps1

# Edit .env with your API keys
notepad .env

# Start the application
py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000
```

### Linux/macOS
```bash
# Make setup script executable
chmod +x setup.sh

# Run the setup script
./setup.sh

# Edit .env with your API keys
nano .env

# Start the application
python -m uvicorn app_new.main:app --reload --host 0.0.0.0 --port 8000
```

### Manual Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your configuration
cp .env.example .env  # Edit with your API keys

# Create admin user
python create_admin.py

# Run the application
python -m uvicorn app_new.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

Create a `.env` file in the root directory:

```env
# Stock Service API Keys
FINNHUB_TOKEN=your_finnhub_api_key
ALPHA_VANTAGE_KEY=your_alpha_vantage_api_key

# Service Configuration
POLL_SECONDS=60
SHOWCASE_REFRESH=300
COOLDOWN_MIN=30
ALPHA_MIN_INTERVAL=13.0

# Application Security
SECRET_KEY=your-secret-key-here
DEBUG=false
```

### Getting API Keys

**Finnhub** (Free tier available):
- Sign up at https://finnhub.io/register
- Get your API key from the dashboard

**Alpha Vantage** (Free tier available):
- Sign up at https://www.alphavantage.co/support/#api-key
- Get your API key instantly

## Dependencies

All dependencies are listed in `requirements.txt`:

- **FastAPI**: Modern web framework
- **Uvicorn**: ASGI server
- **aiohttp**: Async HTTP client for API calls
- **python-dotenv**: Environment variable management
- **psutil**: System monitoring
- **PyJWT**: Authentication tokens
- **Jinja2**: Template engine
- And more...

Install all with: `pip install -r requirements.txt`

## Project Structure

```
cameronpad/
├── app_new/                # Core application
│   ├── api/               # API routes and middleware
│   ├── core/              # Core functionality (auth, db, config)
│   ├── plugins/           # Plugin system
│   └── main.py            # Application entry point
├── plugins/               # Individual plugins
│   ├── stocks/           # Stock monitoring plugin
│   ├── notes/            # Notes plugin
│   ├── journal/          # Journal plugin
│   ├── surf/             # Surf tracker plugin
│   ├── system_monitor/   # System monitoring plugin
│   └── ...
├── templates/             # HTML templates
├── static/               # Static files (CSS, JS, images)
├── data/                 # Database and uploads
├── requirements.txt      # Python dependencies
├── .env                  # Environment configuration (create this)
├── setup.sh             # Linux setup script
├── setup.ps1            # Windows setup script
└── DEPLOYMENT.md        # Production deployment guide
```

## Usage

1. **Access the application**: http://localhost:8000
2. **Login**: Use the admin credentials you created
3. **Stock Monitor**:
   - Navigate to the Stocks plugin
   - Click "Start Service" to begin monitoring
   - View real-time price updates on the showcase

## Development

### Adding a New Plugin

1. Create plugin directory in `plugins/`
2. Create `plugin.py` with plugin class extending `BasePlugin`
3. Create `plugin.yaml` for configuration
4. Implement required methods and routes
5. Restart application to load plugin

See existing plugins for examples.

### Running Tests

```bash
# Run stock service tests
python tests/test_real_api.py

# Run database check
python check_db.py
```

## Production Deployment

### Deployment Options

1. **WinSCP Transfer Method** (Easiest if you have Windows)
   - See **[DEPLOY_WITH_WINSCP.md](DEPLOY_WITH_WINSCP.md)** - Complete guide for transferring files with WinSCP
   - See **[DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)** - Quick checklist for deployment steps
   - After transfer, run: `./deploy_after_winscp.sh` (automated setup)

2. **Full Production Setup**
   - See **[DEPLOYMENT.md](DEPLOYMENT.md)** - Comprehensive production deployment guide
   - Includes: Gunicorn, systemd, Nginx, SSL, backups

### Quick Deploy with WinSCP

```bash
# 1. Use WinSCP to transfer files to Linux server
# 2. SSH into server and run:
cd cameronpad
chmod +x deploy_after_winscp.sh
./deploy_after_winscp.sh
```

This automated script will:
- Backup existing database and config
- Recreate virtual environment
- Install all dependencies
- Set proper permissions
- Start the service

### Production Best Practices

- Use Gunicorn with Uvicorn workers
- Set up systemd service for auto-restart
- Configure Nginx as reverse proxy
- Set up SSL with Let's Encrypt
- Configure firewall rules
- Set up automated backups

## Troubleshooting

### Stock Prices Not Updating

1. Check API keys in `.env` are correct
2. Verify service is running (click "Start Service")
3. Check logs for API errors
4. Verify environment variables are loaded:
   ```bash
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('FINNHUB_TOKEN'))"
   ```

### Database Issues

```bash
# Check database
python check_db.py

# Check database file permissions
ls -la data/
```

### Port Already in Use

```bash
# Find process using port 8000
# Linux:
lsof -i :8000
# Windows:
netstat -ano | findstr :8000

# Kill the process or use a different port
python -m uvicorn app_new.main:app --port 8001
```

## Security Notes

- Change `SECRET_KEY` in `.env` to a random string in production
- Use HTTPS in production (see DEPLOYMENT.md)
- Keep dependencies updated: `pip install -r requirements.txt --upgrade`
- Regularly backup your database
- Use strong passwords for admin accounts

## License

[Your License Here]

## Support

For issues and questions:
1. Check DEPLOYMENT.md for deployment issues
2. Review application logs
3. Verify all environment variables are set correctly

## Contributing

[Your contribution guidelines here]
