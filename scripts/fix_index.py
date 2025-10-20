import json
from pathlib import Path

# Load all theme files
themes_dir = Path("generated_themes")
themes = []

for theme_file in themes_dir.glob("*.json"):
    if theme_file.name != "index.json":
        with open(theme_file, 'r', encoding='utf-8') as f:
            themes.append(json.load(f))

# Create index
index = {
    "version": "1.0.0",
    "theme_count": len(themes),
    "categories": {},
    "themes": []
}

# Group by category
for theme in themes:
    category = theme["category"]
    if category not in index["categories"]:
        index["categories"][category] = 0
    index["categories"][category] += 1
    
    # Add theme summary with correct URLs
    index["themes"].append({
        "id": theme["id"],
        "name": theme["name"],
        "description": theme["description"],
        "category": category,
        "tags": theme["tags"],
        "download_url": f"https://raw.githubusercontent.com/camayuki/theme_marketplace/main/{theme['id']}.json",
        "preview_image": f"https://raw.githubusercontent.com/camayuki/theme_marketplace/main/previews/{theme['id']}.png",
    })

# Save index
index_file = themes_dir / "index.json"
with open(index_file, 'w', encoding='utf-8') as f:
    json.dump(index, f, indent=2)

print(f"✅ Regenerated index.json with {len(themes)} themes")
print(f"📊 Categories: {index['categories']}")
print(f"📁 Saved to: {index_file}")
