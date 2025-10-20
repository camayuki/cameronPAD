# 🎨 CameronPAD Theme Marketplace - GitHub Setup Script
# This script will help you set up your GitHub repository for the theme marketplace

Write-Host "🎨 CameronPAD Theme Marketplace Setup" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan
Write-Host ""

# Check if generated_themes exists
if (-not (Test-Path "generated_themes")) {
    Write-Host "❌ Error: generated_themes folder not found!" -ForegroundColor Red
    Write-Host "   Please run: py scripts\theme_generator.py" -ForegroundColor Yellow
    exit 1
}

# Count themes
$themeCount = (Get-ChildItem "generated_themes\*.json" | Where-Object { $_.Name -ne "index.json" }).Count
Write-Host "✅ Found $themeCount themes in generated_themes/" -ForegroundColor Green
Write-Host ""

# Get user information
Write-Host "📝 GitHub Repository Setup" -ForegroundColor Cyan
Write-Host "-" * 50
$username = Read-Host "Enter your GitHub username"
$repoName = Read-Host "Enter repository name (default: cameronpad-themes)" 

if ([string]::IsNullOrWhiteSpace($repoName)) {
    $repoName = "cameronpad-themes"
}

Write-Host ""
Write-Host "Repository URL will be:" -ForegroundColor Yellow
Write-Host "  https://github.com/$username/$repoName" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Continue? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "❌ Setup cancelled" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "🚀 Setting up Git repository..." -ForegroundColor Cyan

# Navigate to generated_themes
Push-Location generated_themes

try {
    # Initialize git if not already initialized
    if (-not (Test-Path ".git")) {
        Write-Host "  📦 Initializing Git repository..." -ForegroundColor Yellow
        git init
        if ($LASTEXITCODE -ne 0) { throw "Git init failed" }
    }

    # Create README
    Write-Host "  📝 Creating README.md..." -ForegroundColor Yellow
    $readmeContent = @"
# 🎨 CameronPAD Themes

A collection of **$themeCount beautiful themes** for CameronPAD and any web application!

## 🌈 Theme Categories

- 🌑 **Dark Themes** - Perfect for late-night coding
- ☀️ **Light Themes** - Beautiful daytime themes
- 🌌 **Midnight Themes** - Ultra-dark minimal themes
- 🎨 **Pastel Themes** - Soft, gentle colors

## 📥 Installation

### For CameronPAD Users

1. Visit your CameronPAD instance
2. Go to **Themes** → **Marketplace**
3. Browse and install themes with one click!

### For Developers

Use these themes in **any web application**:

``````javascript
// Fetch and apply a theme
fetch('https://raw.githubusercontent.com/$username/$repoName/main/cobalt-0.json')
    .then(response => response.json())
    .then(theme => {
        // Apply CSS variables
        Object.entries(theme.css_variables).forEach(([key, value]) => {
            document.documentElement.style.setProperty(key, value);
        });
    });
``````

### Integration Guides

- ✅ **React** - [See guide](https://github.com/camayuki/cameronPAD/blob/main/THEME_INTEGRATION_GUIDE.md#react)
- ✅ **Vue.js** - [See guide](https://github.com/camayuki/cameronPAD/blob/main/THEME_INTEGRATION_GUIDE.md#vuejs)
- ✅ **WordPress** - [See guide](https://github.com/camayuki/cameronPAD/blob/main/THEME_INTEGRATION_GUIDE.md#wordpress)
- ✅ **Django/Flask** - [See guide](https://github.com/camayuki/cameronPAD/blob/main/THEME_INTEGRATION_GUIDE.md#django--flask)
- ✅ **Vanilla JS** - [See guide](https://github.com/camayuki/cameronPAD/blob/main/THEME_INTEGRATION_GUIDE.md#static-sites)

## 🎨 Theme Format

Each theme is a JSON file with this structure:

``````json
{
  "id": "cobalt-0",
  "name": "Cobalt",
  "description": "A beautiful dark theme",
  "author": "CameronPAD Theme Generator",
  "version": "1.0.0",
  "category": "Dark",
  "tags": ["dark", "blue", "professional"],
  "css_variables": {
    "--primary-bg": "#0a0e1a",
    "--secondary-bg": "#141824",
    "--accent-primary": "#4fc3f7",
    ...
  }
}
``````

## 📋 Browse Themes

See [index.json](./index.json) for the complete theme catalog.

## 🤝 Contributing

Want to add your own theme? We'd love that!

1. Fork this repository
2. Add your theme JSON file
3. Update `index.json`
4. Submit a Pull Request

See our [Contribution Guide](https://github.com/camayuki/cameronPAD/blob/main/THEME_MARKETPLACE_SETUP.md#community-contributions) for details.

## 📜 License

MIT License - Use these themes anywhere, free forever!

## 🔗 Links

- [CameronPAD Project](https://github.com/camayuki/cameronPAD)
- [Theme Integration Guide](https://github.com/camayuki/cameronPAD/blob/main/THEME_INTEGRATION_GUIDE.md)
- [Theme Marketplace Setup](https://github.com/camayuki/cameronPAD/blob/main/THEME_MARKETPLACE_SETUP.md)

## ⭐ Support

If you like these themes, please star this repository!

---

**Generated with ❤️ by CameronPAD Theme Generator**
"@
    
    Set-Content -Path "README.md" -Value $readmeContent

    # Create .gitignore
    Write-Host "  📝 Creating .gitignore..." -ForegroundColor Yellow
    Set-Content -Path ".gitignore" -Value @"
# OS files
.DS_Store
Thumbs.db

# Editor files
.vscode/
.idea/
*.swp
*.swo

# Temporary files
*.tmp
*.bak
"@

    # Add all files
    Write-Host "  ➕ Adding files to Git..." -ForegroundColor Yellow
    git add .
    if ($LASTEXITCODE -ne 0) { throw "Git add failed" }

    # Commit
    Write-Host "  💾 Creating initial commit..." -ForegroundColor Yellow
    git commit -m "🎨 Initial commit: $themeCount beautiful themes for CameronPAD"
    if ($LASTEXITCODE -ne 0) { throw "Git commit failed" }

    # Set branch to main
    Write-Host "  🌿 Setting branch to main..." -ForegroundColor Yellow
    git branch -M main

    Write-Host ""
    Write-Host "✅ Local Git repository ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "=" * 50 -ForegroundColor Cyan
    Write-Host "📋 NEXT STEPS" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1️⃣  Create the GitHub repository:" -ForegroundColor Yellow
    Write-Host "    Go to: https://github.com/new" -ForegroundColor White
    Write-Host "    Repository name: $repoName" -ForegroundColor White
    Write-Host "    Description: Beautiful themes for CameronPAD" -ForegroundColor White
    Write-Host "    ✅ Make it PUBLIC" -ForegroundColor Green
    Write-Host "    ❌ Do NOT initialize with README" -ForegroundColor Red
    Write-Host ""
    Write-Host "2️⃣  Push to GitHub (run this after creating the repo):" -ForegroundColor Yellow
    Write-Host "    cd generated_themes" -ForegroundColor White
    Write-Host "    git remote add origin https://github.com/$username/$repoName.git" -ForegroundColor White
    Write-Host "    git push -u origin main" -ForegroundColor White
    Write-Host ""
    Write-Host "3️⃣  Update CameronPAD to use your marketplace:" -ForegroundColor Yellow
    Write-Host "    Edit: app_new\core\theme_downloader.py" -ForegroundColor White
    Write-Host "    Change the marketplace URL to:" -ForegroundColor White
    Write-Host "    https://raw.githubusercontent.com/$username/$repoName/main/index.json" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "4️⃣  Test your marketplace:" -ForegroundColor Yellow
    Write-Host "    Restart your server and visit:" -ForegroundColor White
    Write-Host "    http://127.0.0.1:8000/themes/marketplace" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "=" * 50 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "💡 Quick command reference saved to: PUSH_COMMANDS.txt" -ForegroundColor Green
    
    # Save push commands to file
    $pushCommands = @"
# Push to GitHub - Run these commands after creating the repository

cd generated_themes
git remote add origin https://github.com/$username/$repoName.git
git push -u origin main

# If you already added the remote, just use:
git push -u origin main

# Repository URL: https://github.com/$username/$repoName
# Raw theme URL: https://raw.githubusercontent.com/$username/$repoName/main/index.json
"@
    Set-Content -Path "PUSH_COMMANDS.txt" -Value $pushCommands

} catch {
    Write-Host ""
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Pop-Location
    exit 1
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "🎉 Setup complete! Follow the steps above to publish your themes." -ForegroundColor Green
Write-Host ""
