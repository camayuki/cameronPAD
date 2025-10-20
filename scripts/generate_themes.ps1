# CameronPAD Theme Generator - Quick Start
# Generates 100 beautiful themes ready for marketplace

Write-Host "🎨 CameronPAD Theme Generator" -ForegroundColor Cyan
Write-Host "=" * 50

# Run the generator
Write-Host "`n📦 Generating 100 themes..." -ForegroundColor Yellow
py scripts\theme_generator.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Themes generated successfully!" -ForegroundColor Green
    Write-Host "`n📁 Output: generated_themes\" -ForegroundColor Cyan
    
    # Show statistics
    $themeCount = (Get-ChildItem generated_themes\*.json -Exclude index.json).Count
    Write-Host "`n📊 Generated $themeCount theme files" -ForegroundColor Cyan
    
    Write-Host "`n🚀 Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Review themes in generated_themes\" -ForegroundColor White
    Write-Host "2. Create GitHub repo: cameronpad-themes" -ForegroundColor White
    Write-Host "3. Push themes to GitHub" -ForegroundColor White
    Write-Host "4. Update theme_downloader.py with your repo URL" -ForegroundColor White
    
    Write-Host "`n📖 See THEME_MARKETPLACE_SETUP.md for full guide" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Error generating themes" -ForegroundColor Red
    exit 1
}
