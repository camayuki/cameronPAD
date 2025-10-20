# 🛍️ Theme Marketplace Guide

## What is the Theme Marketplace?

The Theme Marketplace is your one-stop shop for discovering and installing beautiful themes for CameronPAD. Browse community-created themes, preview them, and install with just one click!

## Features

### 🎨 6 Popular Community Themes Available

1. **Monokai Pro** - Dark theme inspired by the popular Monokai color scheme
2. **Dracula** - Beautiful dark theme with vibrant colors  
3. **Nord** - Arctic, north-bluish minimal color palette
4. **Solarized Light** - Precision warm light theme
5. **Tokyo Night** - Clean dark theme inspired by Tokyo's night
6. **Gruvbox** - Retro groove color scheme with pastel colors

All themes include ratings, download counts, and detailed metadata!

## How to Use

### Access the Marketplace

1. Click **🎨 Themes** in the navigation bar
2. Or visit: http://127.0.0.1:8000/themes/marketplace

### Browse Themes

**Search:** Use the search box to find themes by name
**Filter:** Select category (Dark or Light themes)
**Sort:** Order by Downloads, Rating, or Name

### Install a Theme

1. **Find a theme** you like in the marketplace
2. **Click "⬇️ Install"** button on the theme card
3. **Wait for download** - The theme will be downloaded and installed automatically
4. **Apply immediately** - You'll be asked if you want to apply it right away
   - Click "OK" to apply the theme immediately
   - Click "Cancel" to just install it for later

### Apply an Installed Theme

If you installed a theme but didn't apply it:

1. **Go to Settings** (http://127.0.0.1:8000/settings)
2. **Scroll to "Theme Selection"**
3. **Select your installed theme** from the grid
4. **Click "Apply Theme"**

Or from the Marketplace:

1. **Find the installed theme** (marked with "✅ INSTALLED")
2. **Click "🎨 Apply"** button

## Theme Information

Each theme card shows:

- **Preview** - Visual gradient showing theme colors
- **Rating** - ⭐ Average user rating (out of 5)
- **Downloads** - ⬇️ Number of times downloaded
- **Description** - What makes this theme unique
- **Category** - Dark or Light theme
- **Tags** - Keywords like "vibrant", "minimal", "professional"
- **Author** - Who created the theme
- **Version** - Theme version number

## Advanced Features

### Future Enhancements (Coming Soon)

- **Real-time Preview** - See theme applied before installing
- **Theme Ratings** - Rate themes you've tried
- **Create Custom Themes** - Design and share your own
- **Theme Collections** - Curated theme bundles
- **Auto Dark Mode** - Automatically switch between light/dark based on time
- **Theme Sync** - Your themes across all devices

## Technical Details

### How It Works

1. **Marketplace Catalog** - Themes are stored in a registry (currently sample data)
2. **Download Manager** - Downloads theme JSON from GitHub or CDN
3. **Validation** - Ensures theme has all required CSS variables
4. **Installation** - Saves theme to database
5. **Application** - Updates user preference and reloads page

### Theme Structure

Each theme is a JSON file with:

```json
{
  "id": "theme-name",
  "name": "Theme Display Name",
  "description": "What makes this theme special",
  "author": "Creator Name",
  "version": "1.0.0",
  "category": "Dark",
  "tags": ["modern", "professional"],
  "css_variables": {
    "--primary-bg": "#1a1a1a",
    "--secondary-bg": "#2d2d2d",
    "--accent-primary": "#ff6b6b",
    ...
  }
}
```

### Creating Your Own Theme Repository

Want to host your own themes? Here's how:

1. **Create a GitHub repository** (e.g., `your-username/cameronpad-themes`)
2. **Add theme JSON files** to the `themes/` folder
3. **Update theme_downloader.py** with your repo details:

```python
"repos": [
    {
        "owner": "your-username",
        "repo": "cameronpad-themes",
        "branch": "main",
        "path": "themes"
    }
]
```

4. **Themes auto-appear** in marketplace!

## Troubleshooting

### Theme Won't Install

- **Check internet connection** - Downloads require network access
- **Verify theme URL** - Ensure download URL is accessible
- **Check console** - Look for error messages in browser console

### Theme Looks Broken

- **Clear browser cache** - Force reload with Ctrl+F5
- **Check CSS variables** - Theme might be missing required variables
- **Switch to built-in theme** - Use a safe default theme in Settings

### Can't Uninstall Theme

- **Built-in themes** cannot be uninstalled (space, dark, light, etc.)
- **Only marketplace themes** can be removed
- **Use Settings page** to switch to a different theme first

## API Reference

### Get Marketplace Themes

```javascript
GET /themes/marketplace/api/themes?category=dark&search=tokyo&sort=rating
```

**Response:**
```json
{
  "success": true,
  "themes": [...],
  "count": 6
}
```

### Install Theme

```javascript
POST /themes/marketplace/api/install/tokyo-night
```

**Response:**
```json
{
  "success": true,
  "already_installed": false,
  "message": "Theme installed successfully!",
  "theme": {...},
  "prompt_apply": true
}
```

### Apply Theme

```javascript
POST /api/themes/set
Content-Type: application/json

{
  "theme_id": "tokyo-night"
}
```

## Theme Categories

### Dark Themes
Perfect for late-night coding sessions:
- Monokai Pro
- Dracula
- Nord
- Tokyo Night
- Gruvbox

### Light Themes
Easy on the eyes during daytime:
- Solarized Light

## Popular Themes

### Most Downloaded
1. **Tokyo Night** - 2,500 downloads
2. **Dracula** - 2,100 downloads
3. **Nord** - 1,800 downloads

### Highest Rated
1. **Dracula** - ⭐ 4.9
2. **Tokyo Night** - ⭐ 4.9
3. **Monokai Pro** - ⭐ 4.8

## Security

### Theme Safety

✅ **Themes are safe** because:
- Only CSS variables (no executable code)
- JSON format only
- Validated before installation
- Sandboxed in the app

❌ **Themes CANNOT:**
- Execute JavaScript
- Access your data
- Make network requests
- Modify your files

## Support

**Found a bug?** Report issues in the repository
**Want a feature?** Suggest it in discussions
**Need help?** Check the documentation

---

**Enjoy customizing CameronPAD with beautiful themes!** 🎨
