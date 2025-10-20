# 🚀 Push Theme Marketplace to GitHub

Write-Host "🎨 CameronPAD Theme Marketplace - GitHub Push" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan
Write-Host ""

# Change to theme_marketplace directory
Set-Location "D:\Repositories\theme_marketplace"

# Check if files exist
$jsonFiles = Get-ChildItem "*.json" | Measure-Object
Write-Host "📦 Files ready:" -ForegroundColor Green
Write-Host "   JSON themes: $($jsonFiles.Count)" -ForegroundColor White
Write-Host "   README.md: $(Test-Path README.md)" -ForegroundColor White
Write-Host "   theme-loader.js: $(Test-Path theme-loader.js)" -ForegroundColor White
Write-Host ""

# Git status
Write-Host "📋 Checking Git status..." -ForegroundColor Yellow
git status --short

Write-Host ""
$confirm = Read-Host "Ready to commit and push? (y/n)"

if ($confirm -eq 'y') {
    Write-Host ""
    Write-Host "➕ Adding all files..." -ForegroundColor Yellow
    git add .
    
    Write-Host "💾 Creating commit..." -ForegroundColor Yellow
    git commit -m "🎨 Add 100 beautiful themes for CameronPAD

- Auto-generated themes using color theory
- 15 color schemes (monochrome, analogous, complementary, etc.)
- 4 style categories (dark, light, midnight, pastel)
- Theme loader JavaScript library
- Complete documentation and integration guides
- CDN-ready via jsDelivr

Generated with CameronPAD Theme Generator"
    
    Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Yellow
    git push -u origin main
    
    Write-Host ""
    Write-Host "=" * 50 -ForegroundColor Green
    Write-Host "✅ SUCCESS! Your themes are now live!" -ForegroundColor Green
    Write-Host "=" * 50 -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Repository URL:" -ForegroundColor Cyan
    Write-Host "   https://github.com/camayuki/theme_marketplace" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 Theme Index URL:" -ForegroundColor Cyan
    Write-Host "   https://raw.githubusercontent.com/camayuki/theme_marketplace/main/index.json" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 CDN URL (recommended):" -ForegroundColor Cyan
    Write-Host "   https://cdn.jsdelivr.net/gh/camayuki/theme_marketplace@main/index.json" -ForegroundColor White
    Write-Host ""
    Write-Host "📝 Next Steps:" -ForegroundColor Yellow
    Write-Host "   1. Update CameronPAD to use your marketplace URL" -ForegroundColor White
    Write-Host "   2. Restart your server" -ForegroundColor White
    Write-Host "   3. Visit http://127.0.0.1:8000/themes/marketplace" -ForegroundColor White
    Write-Host "   4. Share your themes with the world! 🎉" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Push cancelled" -ForegroundColor Red
    Write-Host "   Run this script again when ready" -ForegroundColor Yellow
}

# Return to original directory
Set-Location "D:\Repositories\cameronPAD_main2"
