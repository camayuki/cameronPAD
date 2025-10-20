"""
CameronPAD Theme Generator
Automatically generates beautiful themes with various color schemes
"""

import json
import colorsys
import random
from pathlib import Path
from typing import Dict, List, Tuple


class ThemeGenerator:
    """Generate beautiful themes automatically"""
    
    # Base theme categories
    THEME_STYLES = {
        "dark": {
            "bg_lightness": (0.05, 0.15),
            "text_lightness": (0.85, 0.95),
        },
        "light": {
            "bg_lightness": (0.90, 0.98),
            "text_lightness": (0.15, 0.30),
        },
        "midnight": {
            "bg_lightness": (0.02, 0.08),
            "text_lightness": (0.88, 0.98),
        },
        "pastel": {
            "bg_lightness": (0.92, 0.97),
            "text_lightness": (0.25, 0.40),
            "saturation_boost": 0.7,
        },
    }
    
    # Color schemes
    COLOR_SCHEMES = {
        "monochrome": {"hues": [0], "variation": 0},
        "analogous": {"hues": [0, 30, 330], "variation": 10},
        "complementary": {"hues": [0, 180], "variation": 15},
        "triadic": {"hues": [0, 120, 240], "variation": 10},
        "tetradic": {"hues": [0, 90, 180, 270], "variation": 10},
        "warm": {"hues": [0, 30, 60], "variation": 15},
        "cool": {"hues": [180, 210, 240], "variation": 15},
        "neon": {"hues": [300, 180, 60], "variation": 20, "saturation": 0.9},
        "earth": {"hues": [30, 40, 20], "variation": 10, "saturation": 0.5},
        "ocean": {"hues": [200, 220, 240], "variation": 15, "saturation": 0.7},
        "sunset": {"hues": [0, 20, 280], "variation": 15, "saturation": 0.8},
        "forest": {"hues": [120, 140, 100], "variation": 10, "saturation": 0.6},
        "lavender": {"hues": [270, 290, 250], "variation": 15, "saturation": 0.6},
        "cherry": {"hues": [350, 10, 330], "variation": 15, "saturation": 0.7},
        "mint": {"hues": [160, 140, 180], "variation": 15, "saturation": 0.6},
    }
    
    def __init__(self):
        self.generated_count = 0
    
    def hsl_to_hex(self, h: float, s: float, l: float) -> str:
        """Convert HSL to hex color"""
        r, g, b = colorsys.hls_to_rgb(h / 360, l, s)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    def generate_color_palette(self, base_hue: int, scheme: dict, style: dict) -> Dict[str, str]:
        """Generate a complete color palette"""
        hues = scheme["hues"]
        variation = scheme.get("variation", 10)
        scheme_saturation = scheme.get("saturation", 0.7)
        
        # Adjust base hue
        adjusted_hues = [(base_hue + h) % 360 for h in hues]
        
        # Background colors
        bg_lightness = random.uniform(*style["bg_lightness"])
        secondary_bg_lightness = bg_lightness + random.uniform(0.02, 0.05)
        accent_bg_lightness = bg_lightness + random.uniform(0.08, 0.15)
        
        # Text colors
        text_lightness = random.uniform(*style["text_lightness"])
        secondary_text_lightness = text_lightness - random.uniform(0.15, 0.25)
        
        # Generate palette
        palette = {
            "--primary-bg": self.hsl_to_hex(
                adjusted_hues[0] + random.randint(-variation, variation),
                scheme_saturation * 0.3,
                bg_lightness
            ),
            "--secondary-bg": self.hsl_to_hex(
                adjusted_hues[0] + random.randint(-variation, variation),
                scheme_saturation * 0.25,
                secondary_bg_lightness
            ),
            "--accent-bg": self.hsl_to_hex(
                adjusted_hues[0] + random.randint(-variation, variation),
                scheme_saturation * 0.4,
                accent_bg_lightness
            ),
            "--text-primary": self.hsl_to_hex(
                adjusted_hues[0] + random.randint(-variation, variation),
                0.1,
                text_lightness
            ),
            "--text-secondary": self.hsl_to_hex(
                adjusted_hues[0] + random.randint(-variation, variation),
                0.15,
                secondary_text_lightness
            ),
        }
        
        # Accent colors from other hues
        accent_hues = adjusted_hues[1:] if len(adjusted_hues) > 1 else adjusted_hues * 3
        
        palette["--accent-primary"] = self.hsl_to_hex(
            accent_hues[0] + random.randint(-variation, variation),
            scheme_saturation,
            0.6 if style["bg_lightness"][0] < 0.5 else 0.5
        )
        
        palette["--accent-secondary"] = self.hsl_to_hex(
            accent_hues[1 % len(accent_hues)] + random.randint(-variation, variation),
            scheme_saturation * 0.9,
            0.65 if style["bg_lightness"][0] < 0.5 else 0.45
        )
        
        palette["--accent-tertiary"] = self.hsl_to_hex(
            accent_hues[2 % len(accent_hues)] + random.randint(-variation, variation),
            scheme_saturation * 0.85,
            0.55 if style["bg_lightness"][0] < 0.5 else 0.5
        )
        
        # Status colors
        palette["--danger"] = self.hsl_to_hex(0, 0.8, 0.55)
        palette["--warning"] = self.hsl_to_hex(40, 0.9, 0.55)
        palette["--success"] = self.hsl_to_hex(120, 0.6, 0.5)
        
        # Card and border colors
        card_lightness = bg_lightness + random.uniform(0.01, 0.03)
        border_lightness = bg_lightness + random.uniform(0.1, 0.2)
        
        palette["--card-bg"] = f"rgba{self._hex_to_rgba(palette['--secondary-bg'], 0.9)}"
        palette["--border-color"] = self.hsl_to_hex(
            adjusted_hues[0],
            scheme_saturation * 0.3,
            border_lightness
        )
        
        # Glow effects
        palette["--glow-color"] = f"rgba{self._hex_to_rgba(palette['--accent-primary'], 0.3)}"
        palette["--purple-glow"] = f"rgba{self._hex_to_rgba(palette['--accent-secondary'], 0.3)}"
        
        return palette
    
    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        """Convert hex to rgba tuple string"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"({r}, {g}, {b}, {alpha})"
    
    def generate_theme_name(self, style: str, scheme: str, hue: int) -> str:
        """Generate a creative theme name"""
        
        # Color names by hue range
        color_names = {
            (0, 15): ["Crimson", "Ruby", "Cardinal", "Scarlet"],
            (15, 45): ["Coral", "Tangerine", "Amber", "Peach"],
            (45, 75): ["Golden", "Honey", "Butterscotch", "Marigold"],
            (75, 105): ["Lime", "Chartreuse", "Olive", "Sage"],
            (105, 165): ["Emerald", "Jade", "Mint", "Viridian"],
            (165, 195): ["Cyan", "Turquoise", "Teal", "Aqua"],
            (195, 255): ["Azure", "Cobalt", "Sapphire", "Navy"],
            (255, 285): ["Indigo", "Violet", "Purple", "Plum"],
            (285, 315): ["Magenta", "Fuchsia", "Orchid", "Lavender"],
            (315, 360): ["Rose", "Pink", "Blush", "Cherry"],
        }
        
        # Find color name
        color_name = "Cosmic"
        for (start, end), names in color_names.items():
            if start <= hue < end:
                color_name = random.choice(names)
                break
        
        # Style modifiers
        style_mods = {
            "dark": ["Night", "Shadow", "Twilight", "Dusk", "Eclipse"],
            "light": ["Day", "Dawn", "Bright", "Morning", "Radiant"],
            "midnight": ["Midnight", "Nocturne", "Deep", "Void", "Abyss"],
            "pastel": ["Soft", "Gentle", "Dream", "Cloud", "Mist"],
        }
        
        style_mod = random.choice(style_mods.get(style, ["Neo"]))
        
        # Combine
        templates = [
            f"{color_name} {style_mod}",
            f"{style_mod} {color_name}",
            f"{color_name}",
        ]
        
        return random.choice(templates)
    
    def generate_theme(self, style_name: str, scheme_name: str, base_hue: int = None) -> dict:
        """Generate a complete theme"""
        if base_hue is None:
            base_hue = random.randint(0, 359)
        
        style = self.THEME_STYLES[style_name]
        scheme = self.COLOR_SCHEMES[scheme_name]
        
        theme_name = self.generate_theme_name(style_name, scheme_name, base_hue)
        theme_id = f"{theme_name.lower().replace(' ', '-')}-{self.generated_count}"
        
        palette = self.generate_color_palette(base_hue, scheme, style)
        
        # Create theme object
        theme = {
            "id": theme_id,
            "name": theme_name,
            "description": f"A beautiful {style_name} theme with {scheme_name} color harmony",
            "author": "CameronPAD Theme Generator",
            "version": "1.0.0",
            "category": "Dark" if style["bg_lightness"][0] < 0.5 else "Light",
            "tags": [style_name, scheme_name, "generated", "auto"],
            "css_variables": palette,
            "base_hue": base_hue,
            "style": style_name,
            "scheme": scheme_name,
        }
        
        self.generated_count += 1
        return theme
    
    def generate_theme_collection(self, count: int = 50) -> List[dict]:
        """Generate a collection of diverse themes"""
        themes = []
        
        # Generate themes with different combinations
        for _ in range(count):
            style = random.choice(list(self.THEME_STYLES.keys()))
            scheme = random.choice(list(self.COLOR_SCHEMES.keys()))
            hue = random.randint(0, 359)
            
            theme = self.generate_theme(style, scheme, hue)
            themes.append(theme)
        
        return themes
    
    def save_theme_to_file(self, theme: dict, output_dir: Path):
        """Save theme to JSON file"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Remove extra metadata before saving
        theme_data = {
            "id": theme["id"],
            "name": theme["name"],
            "description": theme["description"],
            "author": theme["author"],
            "version": theme["version"],
            "category": theme["category"],
            "tags": theme["tags"],
            "css_variables": theme["css_variables"],
        }
        
        file_path = output_dir / f"{theme['id']}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(theme_data, f, indent=2)
        
        return file_path
    
    def generate_marketplace_index(self, themes: List[dict], output_file: Path):
        """Generate index file for marketplace"""
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
            
            # Add theme summary to index
            index["themes"].append({
                "id": theme["id"],
                "name": theme["name"],
                "description": theme["description"],
                "category": category,
                "tags": theme["tags"],
                "download_url": f"https://raw.githubusercontent.com/camayuki/theme_marketplace/main/{theme['id']}.json",
                "preview_image": f"https://raw.githubusercontent.com/camayuki/theme_marketplace/main/previews/{theme['id']}.png",
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
        
        return index


def main():
    """Generate theme collection"""
    generator = ThemeGenerator()
    
    print("🎨 CameronPAD Theme Generator")
    print("=" * 50)
    
    # Generate themes
    print("\n📦 Generating theme collection...")
    themes = generator.generate_theme_collection(count=100)
    print(f"✅ Generated {len(themes)} themes")
    
    # Save to files
    output_dir = Path("generated_themes")
    print(f"\n💾 Saving themes to {output_dir}/...")
    
    for theme in themes:
        file_path = generator.save_theme_to_file(theme, output_dir)
        print(f"  ✓ {theme['name']} → {file_path.name}")
    
    # Generate index
    index_file = output_dir / "index.json"
    print(f"\n📋 Generating marketplace index...")
    index = generator.generate_marketplace_index(themes, index_file)
    print(f"✅ Index saved to {index_file}")
    
    # Print statistics
    print("\n📊 Statistics:")
    print(f"  Total themes: {len(themes)}")
    for category, count in index["categories"].items():
        print(f"  {category}: {count}")
    
    print("\n🎉 Done! Themes ready for marketplace.")
    print(f"\n📁 Output directory: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
