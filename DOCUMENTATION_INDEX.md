# 📚 Documentation Index - CameronPAD

Quick reference to all deployment and setup documentation.

## 🚀 Quick Start Guides

### For Development (Local Testing)

| Platform | Script | Description |
|----------|--------|-------------|
| **Windows** | `setup.ps1` | Automated setup for Windows |
| **Linux/Mac** | `setup.sh` | Automated setup for Unix systems |

**Usage:**
```powershell
# Windows
.\setup.ps1

# Linux/Mac
chmod +x setup.sh && ./setup.sh
```

### For Production (Linux Server)

| Method | Best For | Documentation |
|--------|----------|---------------|
| **WinSCP Transfer** | Windows → Linux | `DEPLOY_WITH_WINSCP.md`, `WINSCP_GUIDE.md` |
| **Full Production** | New server setup | `DEPLOYMENT.md` |
| **Quick Deploy** | Existing setup | `DEPLOY_CHECKLIST.md` |

## 📖 Documentation Files

### Essential Reading

1. **README.md** - Start here!
   - Project overview
   - Features list
   - Quick start guide
   - Basic usage

2. **requirements.txt** - Dependencies
   - All Python packages needed
   - Use: `pip install -r requirements.txt`

### Deployment Guides (Choose Your Path)

#### Path A: WinSCP Transfer (Easiest)

Perfect if you're developing on Windows and deploying to Linux.

1. **WINSCP_GUIDE.md** - WinSCP basics
   - How to connect
   - What to transfer
   - Troubleshooting
   
2. **DEPLOY_CHECKLIST.md** - Quick checklist
   - Step-by-step checklist
   - Copy-paste commands
   - Quick troubleshooting

3. **DEPLOY_WITH_WINSCP.md** - Complete guide
   - Detailed instructions
   - Backup procedures
   - Full troubleshooting

#### Path B: Full Production Deployment

Perfect for new server or professional production setup.

1. **DEPLOYMENT.md** - Comprehensive guide
   - Production best practices
   - Systemd service setup
   - Nginx configuration
   - SSL/HTTPS setup
   - Monitoring and backups

### Configuration

1. **.env** (you create this)
   ```env
   FINNHUB_TOKEN=your_actual_token
   ALPHA_VANTAGE_KEY=your_actual_key
   POLL_SECONDS=60
   SHOWCASE_REFRESH=300
   ```

2. **Environment Variables**
   - Stock API keys
   - Service configuration
   - Application secrets

## 🛠️ Helper Scripts

### Pre-Deployment (Windows)

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `pre_deploy_check.ps1` | Verify ready to deploy | Before WinSCP transfer |
| `setup.ps1` | Initial setup | First time on Windows |

**Example:**
```powershell
# Check if ready to deploy
.\pre_deploy_check.ps1
```

### Post-Deployment (Linux)

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `deploy_after_winscp.sh` | Auto-deployment | After WinSCP transfer |
| `setup.sh` | Initial setup | First time on Linux |

**Example:**
```bash
# After WinSCP transfer
chmod +x deploy_after_winscp.sh
./deploy_after_winscp.sh
```

## 🎯 Common Scenarios

### Scenario 1: First Time Setup (Development)

**Windows:**
```powershell
.\setup.ps1
notepad .env  # Add your API keys
py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000
```

**Linux:**
```bash
chmod +x setup.sh && ./setup.sh
nano .env  # Add your API keys
python -m uvicorn app_new.main:app --reload --host 0.0.0.0 --port 8000
```

### Scenario 2: Deploy to Linux Server (from Windows)

```powershell
# 1. Verify ready
.\pre_deploy_check.ps1

# 2. Use WinSCP to transfer files
#    See: WINSCP_GUIDE.md

# 3. SSH into server and run:
ssh user@server
cd cameronpad
chmod +x deploy_after_winscp.sh
./deploy_after_winscp.sh
```

See detailed steps: **DEPLOY_WITH_WINSCP.md**

### Scenario 3: Update Existing Deployment

```bash
# On Linux server:
cd cameronpad
sudo systemctl stop cameronpad
# Use WinSCP to transfer changed files
./deploy_after_winscp.sh
```

See checklist: **DEPLOY_CHECKLIST.md**

### Scenario 4: Fresh Production Server

```bash
# Transfer files, then:
cd cameronpad
./setup.sh

# Follow full production setup
```

See guide: **DEPLOYMENT.md**

## 📋 File Structure Reference

```
cameronpad/
├── Documentation (Start Here!)
│   ├── README.md                    # Main documentation
│   ├── DEPLOYMENT.md                # Full production guide
│   ├── DEPLOY_WITH_WINSCP.md        # WinSCP deployment guide
│   ├── DEPLOY_CHECKLIST.md          # Quick checklist
│   ├── WINSCP_GUIDE.md              # WinSCP instructions
│   └── DOCUMENTATION_INDEX.md       # This file
│
├── Setup Scripts
│   ├── setup.ps1                    # Windows setup
│   ├── setup.sh                     # Linux setup
│   ├── pre_deploy_check.ps1         # Pre-deploy verification (Windows)
│   └── deploy_after_winscp.sh       # Post-transfer deployment (Linux)
│
├── Configuration
│   ├── requirements.txt             # Python dependencies
│   ├── .env                         # Environment variables (YOU CREATE)
│   └── *.yaml                       # Plugin configurations
│
├── Application Code
│   ├── app_new/                     # Core application
│   ├── plugins/                     # Plugin modules
│   ├── templates/                   # HTML templates
│   ├── static/                      # CSS, JS, images
│   └── data/                        # Database and uploads
│
└── Utilities
    ├── create_admin.py              # Create admin user
    ├── check_db.py                  # Database verification
    └── migrate_all_data.py          # Data migration
```

## 🔑 Getting API Keys

### Finnhub (Free tier: 60 calls/minute)
1. Visit: https://finnhub.io/register
2. Sign up with email
3. Get API key from dashboard
4. Add to `.env`: `FINNHUB_TOKEN=your_key_here`

### Alpha Vantage (Free tier: 5 calls/minute)
1. Visit: https://www.alphavantage.co/support/#api-key
2. Enter email
3. Receive API key instantly
4. Add to `.env`: `ALPHA_VANTAGE_KEY=your_key_here`

## ❓ Which Guide Should I Use?

### Choose Based on Your Situation:

| Your Situation | Recommended Guide |
|----------------|-------------------|
| New to the project | **README.md** |
| Setting up on Windows for dev | **setup.ps1** → README.md |
| Setting up on Linux for dev | **setup.sh** → README.md |
| Deploying from Windows to Linux | **WINSCP_GUIDE.md** → **DEPLOY_WITH_WINSCP.md** |
| Need quick reference for deploy | **DEPLOY_CHECKLIST.md** |
| Setting up production server | **DEPLOYMENT.md** |
| Stock prices not working | Check .env has real keys, not placeholders |
| Service won't start | Check systemd logs: `sudo journalctl -u cameronpad -f` |
| Dependencies issues | Run: `pip install -r requirements.txt` |

## 🆘 Troubleshooting Quick Links

| Problem | Solution |
|---------|----------|
| API Keys not loading | Check `.env` file, verify no placeholders |
| Module not found | Run `pip install -r requirements.txt` |
| Permission denied | Run `sudo chown -R user:user /path/to/cameronpad` |
| Port already in use | Check with `netstat -tulpn \| grep 8000`, kill process |
| Database errors | Check `data/` permissions: `chmod 755 data/` |
| WinSCP won't connect | Verify SSH works: `ssh user@server-ip` |
| Service won't start | Check logs: `sudo journalctl -u cameronpad -n 50` |

## 📞 Support Resources

1. **Check Documentation**: Start with README.md
2. **Review Logs**: Application logs show detailed errors
3. **Verify Configuration**: Run pre-deployment checks
4. **Check Dependencies**: Ensure all packages installed

## 🔄 Update Workflow

### Regular Updates (Code Changes Only)

```bash
# Development (Windows)
1. Make changes
2. Test locally
3. .\pre_deploy_check.ps1

# Deployment (Linux)
4. WinSCP transfer
5. ./deploy_after_winscp.sh
```

### Major Updates (Dependencies Changed)

```bash
# Update requirements.txt, then:
pip install -r requirements.txt --upgrade
sudo systemctl restart cameronpad
```

## 🎓 Learning Path

### For New Users:
1. Start: **README.md** (Overview)
2. Setup: **setup.ps1** or **setup.sh** (Get running locally)
3. Configure: Edit `.env` with API keys
4. Test: Run locally, verify stock service works
5. Deploy: **WINSCP_GUIDE.md** (Move to server)

### For Production:
1. Development: Follow "For New Users" first
2. Server prep: **DEPLOYMENT.md** (systemd, nginx)
3. Deploy: **DEPLOY_WITH_WINSCP.md**
4. Monitor: Check logs and service status
5. Maintain: Regular backups, updates

## 📊 Documentation Quick Stats

- **Total Docs**: 7 markdown files
- **Setup Scripts**: 4 (2 Windows, 2 Linux)
- **Deployment Methods**: 2 (WinSCP, Full Production)
- **Time to Deploy**: ~10-15 minutes with automated scripts
- **Time to Setup**: ~5 minutes with setup scripts

---

**Remember**: Start with **README.md** if you're new, or **DEPLOY_CHECKLIST.md** if you're ready to deploy!
