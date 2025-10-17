# 🚀 CameronPAD Local Development Quick Start

## Super Easy Setup (3 Commands!)

1. **Install Dependencies**
   ```powershell
   # Source the development commands
   . .\scripts\dev_commands.ps1
   
   # Install everything you need
   Install-CameronPAD
   ```

2. **Setup Environment**
   ```powershell
   # Create database and default users
   Setup-CameronPAD
   ```

3. **Start the Server**
   ```powershell
   # Start the development server
   Start-CameronPAD
   # OR just type: cameron
   ```

4. **Open in Browser**
   - 🌐 **Main Site**: http://127.0.0.1:8000
   - Login with: **admin** / **admin123!**

## 🎯 What You Get

### Instant Access
- **Login Required**: Every page requires authentication (as requested!)
- **Admin Panel**: Full user management at `/admin`
- **Beautiful Space Theme**: Animated space background with cosmic UI
- **Auto-Reload**: Changes to code automatically refresh the server

### Default Accounts
- **Admin**: `admin` / `admin123!` (can create/manage users)
- **Test User**: `testuser` / `test123!` (regular user)

### Development Features
- 🔄 **Hot Reload**: Edit files, see changes instantly
- 🐛 **Debug Mode**: Detailed error messages and logging
- 📚 **API Docs**: Auto-generated docs at `/docs`
- 🗃️ **SQLite Database**: Local file-based database (no setup needed)

## 🎮 Quick Commands

After sourcing the commands with `. .\scripts\dev_commands.ps1`:

```powershell
# Start server (all of these work)
Start-CameronPAD
cameron
cam

# Open in browser
cameron-open        # Main site
cameron-admin       # Admin panel  
cameron-docs        # API documentation

# Management
cameron-setup       # Setup/reset environment
cameron-reset       # Reset database
cameron-install     # Install dependencies
cameron-logs        # View recent logs
```

## 🔧 File Structure for Development

```
cameronpad/
├── app_new/           # Main application
├── plugins/           # Plugin system
├── templates/         # HTML templates (space themed!)
├── scripts/           # Development scripts
├── data/             # Local database & uploads
├── logs/             # Development logs
└── config/           # Configuration files
```

## 🌌 Space Theme Features

- **Animated Background**: Floating particles and cosmic gradients
- **Glowing Elements**: Buttons and cards with space-like glows
- **Cosmic Colors**: Blues, purples, and cosmic accent colors
- **Smooth Animations**: Hover effects and transitions
- **Responsive Design**: Works on desktop and mobile

## 🔐 Security Features

- **Mandatory Login**: No access without authentication
- **Role-Based Access**: Admin, user, moderator roles
- **JWT Tokens**: Secure session management
- **Password Hashing**: Bcrypt password protection
- **Rate Limiting**: Protection against brute force attacks

## 🚨 Troubleshooting

### Can't Start Server?
```powershell
# Make sure dependencies are installed
Install-CameronPAD

# Check if setup was run
Setup-CameronPAD
```

### Database Issues?
```powershell
# Reset everything
Reset-CameronPAD
```

### Port Already in Use?
- Close other applications using port 8000
- Or change port in `scripts/dev_server.py`

### Import Errors?
```powershell
# Reinstall dependencies
Install-CameronPAD
```

## 📱 Mobile Testing

The space theme is responsive! Test on mobile:
1. Find your computer's IP address
2. Access from phone: `http://YOUR_IP:8000`
3. Make sure firewall allows port 8000

## 🎉 You're Ready!

No more deploying to Hetzner VM for testing! You now have:
- ✅ Mandatory login system
- ✅ Beautiful space-themed UI
- ✅ Local development server
- ✅ Admin user management
- ✅ Auto-reload for development
- ✅ Easy PowerShell commands

Just run `cameron` and start developing! 🚀