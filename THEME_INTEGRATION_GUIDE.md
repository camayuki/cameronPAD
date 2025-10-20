# 🎨 How to Add CameronPAD Themes to Your Website

This guide shows developers how to integrate themes from the CameronPAD marketplace into **any web application**.

---

## Quick Start (5 Minutes)

### Step 1: Set Up CSS Variables

Add this to your main CSS file:

```css
:root {
    /* Backgrounds */
    --primary-bg: #0a0e1a;
    --secondary-bg: #1a1f35;
    --accent-bg: #2d3561;
    --card-bg: rgba(26, 31, 53, 0.8);
    
    /* Borders */
    --border-color: #3d4785;
    
    /* Text */
    --text-primary: #e8eaed;
    --text-secondary: #9aa0a6;
    
    /* Accents */
    --accent-primary: #4fc3f7;
    --accent-secondary: #ab47bc;
    --accent-tertiary: #66bb6a;
    
    /* Status */
    --danger: #f44336;
    --warning: #ff9800;
    --success: #4caf50;
    
    /* Effects */
    --glow-color: rgba(79, 195, 247, 0.3);
    --purple-glow: rgba(171, 71, 188, 0.3);
}
```

### Step 2: Use Variables in Your CSS

Replace hardcoded colors with variables:

```css
/* Before */
body {
    background: #0a0e1a;
    color: #e8eaed;
}

/* After */
body {
    background: var(--primary-bg);
    color: var(--text-primary);
}
```

### Step 3: Load a Theme

```javascript
// Fetch theme from marketplace
fetch('https://raw.githubusercontent.com/camayuki/cameronpad-themes/main/themes/crimson-night-1.json')
    .then(r => r.json())
    .then(theme => applyTheme(theme));

function applyTheme(theme) {
    const root = document.documentElement;
    const vars = theme.css_variables;
    
    for (const [key, value] of Object.entries(vars)) {
        root.style.setProperty(key, value);
    }
}
```

**Done!** Your site now supports themes. 🎉

---

## Full Integration Guide

### For Static Sites (HTML/CSS/JS)

#### 1. Create Theme Switcher HTML

```html
<div class="theme-selector">
    <select id="themeSelect">
        <option value="">Choose a theme...</option>
    </select>
</div>
```

#### 2. Load Available Themes

```javascript
// Load theme list from marketplace
async function loadThemes() {
    const response = await fetch(
        'https://raw.githubusercontent.com/camayuki/cameronpad-themes/main/index.json'
    );
    const data = await response.json();
    
    const select = document.getElementById('themeSelect');
    data.themes.forEach(theme => {
        const option = document.createElement('option');
        option.value = theme.download_url;
        option.textContent = theme.name;
        select.appendChild(option);
    });
}

loadThemes();
```

#### 3. Apply Selected Theme

```javascript
document.getElementById('themeSelect').addEventListener('change', async (e) => {
    if (!e.target.value) return;
    
    const response = await fetch(e.target.value);
    const theme = await response.json();
    
    applyTheme(theme);
    localStorage.setItem('selectedTheme', e.target.value);
});

// Restore saved theme on page load
window.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('selectedTheme');
    if (saved) {
        document.getElementById('themeSelect').value = saved;
        document.getElementById('themeSelect').dispatchEvent(new Event('change'));
    }
});
```

---

### For React Apps

#### 1. Install Dependencies

```bash
npm install
```

#### 2. Create Theme Context

```jsx
// contexts/ThemeContext.js
import React, { createContext, useState, useEffect } from 'react';

export const ThemeContext = createContext();

export function ThemeProvider({ children }) {
    const [theme, setTheme] = useState(null);
    const [themes, setThemes] = useState([]);
    
    useEffect(() => {
        // Load available themes
        fetch('https://raw.githubusercontent.com/camayuki/cameronpad-themes/main/index.json')
            .then(r => r.json())
            .then(data => setThemes(data.themes));
        
        // Restore saved theme
        const saved = localStorage.getItem('selectedThemeUrl');
        if (saved) {
            loadTheme(saved);
        }
    }, []);
    
    const loadTheme = async (url) => {
        const response = await fetch(url);
        const themeData = await response.json();
        setTheme(themeData);
        applyTheme(themeData);
        localStorage.setItem('selectedThemeUrl', url);
    };
    
    const applyTheme = (themeData) => {
        const root = document.documentElement;
        Object.entries(themeData.css_variables).forEach(([key, value]) => {
            root.style.setProperty(key, value);
        });
    };
    
    return (
        <ThemeContext.Provider value={{ theme, themes, loadTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}
```

#### 3. Use in Components

```jsx
// App.js
import { ThemeProvider } from './contexts/ThemeContext';

function App() {
    return (
        <ThemeProvider>
            <YourApp />
        </ThemeProvider>
    );
}

// ThemeSelector.js
import { useContext } from 'react';
import { ThemeContext } from './contexts/ThemeContext';

function ThemeSelector() {
    const { themes, loadTheme } = useContext(ThemeContext);
    
    return (
        <select onChange={e => loadTheme(e.target.value)}>
            <option>Choose theme...</option>
            {themes.map(t => (
                <option key={t.id} value={t.download_url}>
                    {t.name}
                </option>
            ))}
        </select>
    );
}
```

---

### For Vue.js Apps

#### 1. Create Theme Plugin

```javascript
// plugins/theme.js
export default {
    install(app) {
        const theme = {
            current: null,
            available: [],
            
            async loadThemes() {
                const response = await fetch(
                    'https://raw.githubusercontent.com/camayuki/cameronpad-themes/main/index.json'
                );
                const data = await response.json();
                this.available = data.themes;
            },
            
            async apply(url) {
                const response = await fetch(url);
                const themeData = await response.json();
                this.current = themeData;
                
                const root = document.documentElement;
                Object.entries(themeData.css_variables).forEach(([key, value]) => {
                    root.style.setProperty(key, value);
                });
                
                localStorage.setItem('selectedThemeUrl', url);
            }
        };
        
        app.config.globalProperties.$theme = theme;
        app.provide('theme', theme);
    }
};
```

#### 2. Use in main.js

```javascript
import { createApp } from 'vue';
import App from './App.vue';
import themePlugin from './plugins/theme';

const app = createApp(App);
app.use(themePlugin);
app.mount('#app');
```

#### 3. Use in Components

```vue
<template>
    <select @change="changeTheme">
        <option v-for="theme in $theme.available" :key="theme.id" :value="theme.download_url">
            {{ theme.name }}
        </option>
    </select>
</template>

<script>
export default {
    mounted() {
        this.$theme.loadThemes();
    },
    methods: {
        changeTheme(e) {
            this.$theme.apply(e.target.value);
        }
    }
};
</script>
```

---

### For WordPress Sites

#### 1. Create Custom Plugin

```php
<?php
/*
Plugin Name: CameronPAD Themes
Description: Add CameronPAD marketplace themes to your site
Version: 1.0.0
*/

function cameronpad_themes_enqueue() {
    wp_enqueue_script(
        'cameronpad-themes',
        plugins_url('themes.js', __FILE__),
        [],
        '1.0.0',
        true
    );
}
add_action('wp_enqueue_scripts', 'cameronpad_themes_enqueue');

function cameronpad_themes_menu() {
    add_theme_page(
        'Theme Marketplace',
        'Marketplace',
        'edit_theme_options',
        'cameronpad-themes',
        'cameronpad_themes_page'
    );
}
add_action('admin_menu', 'cameronpad_themes_menu');

function cameronpad_themes_page() {
    ?>
    <div class="wrap">
        <h1>Theme Marketplace</h1>
        <select id="themeSelect"></select>
    </div>
    <script>
        // Load themes...
    </script>
    <?php
}
```

---

### For Django/Flask Apps

#### Python Backend

```python
# views.py
import requests
from django.http import JsonResponse

def get_marketplace_themes(request):
    """Proxy marketplace themes"""
    response = requests.get(
        'https://raw.githubusercontent.com/camayuki/cameronpad-themes/main/index.json'
    )
    return JsonResponse(response.json())

def get_theme(request, theme_id):
    """Get specific theme"""
    response = requests.get(
        f'https://raw.githubusercontent.com/camayuki/cameronpad-themes/main/themes/{theme_id}.json'
    )
    return JsonResponse(response.json())
```

#### Template

```html
<!-- base.html -->
<style id="theme-vars">
    :root {
        /* Default vars... */
    }
</style>

<script>
fetch('/api/themes')
    .then(r => r.json())
    .then(data => {
        // Populate theme selector
    });
</script>
```

---

## Advanced Features

### 1. Theme Preview (Before Applying)

```javascript
function previewTheme(theme) {
    const iframe = document.createElement('iframe');
    iframe.style.width = '100%';
    iframe.style.height = '400px';
    
    iframe.onload = function() {
        const iframeDoc = iframe.contentDocument;
        applyThemeToDocument(iframeDoc, theme);
    };
    
    iframe.src = 'preview.html';
    document.getElementById('preview-container').appendChild(iframe);
}
```

### 2. Smooth Theme Transitions

```css
* {
    transition: background-color 0.3s ease,
                color 0.3s ease,
                border-color 0.3s ease;
}
```

### 3. Dark Mode Auto-Detection

```javascript
// Auto-select dark/light theme based on system preference
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

if (prefersDark) {
    loadTheme('dark-theme-url');
} else {
    loadTheme('light-theme-url');
}
```

### 4. Theme Customization

```javascript
function customizeTheme(baseTheme, customizations) {
    const customTheme = { ...baseTheme };
    customTheme.css_variables = {
        ...baseTheme.css_variables,
        ...customizations
    };
    return customTheme;
}

// Usage
const myTheme = customizeTheme(baseTheme, {
    '--accent-primary': '#ff0000'
});
```

---

## Requirements Checklist

For themes to work properly, your CSS must:

- [ ] Use CSS variables (not hardcoded colors)
- [ ] Include all 14 required variable names
- [ ] Apply variables to all UI elements
- [ ] Support rgba values for transparency
- [ ] Handle both light and dark themes

---

## Common Issues

### Theme Not Applying?

**Check 1**: Are CSS variables defined?
```javascript
console.log(getComputedStyle(document.documentElement).getPropertyValue('--primary-bg'));
```

**Check 2**: Are colors used in CSS?
```css
/* Wrong */
background: #1a1a1a;

/* Right */
background: var(--primary-bg);
```

**Check 3**: CORS errors?
```javascript
// Use a CORS proxy if needed
const proxy = 'https://corsproxy.io/?';
fetch(proxy + theme_url);
```

---

## Best Practices

1. **Always provide fallback colors**
   ```css
   color: var(--text-primary, #ffffff);
   ```

2. **Save user preference**
   ```javascript
   localStorage.setItem('theme', themeId);
   ```

3. **Load theme before page render** (avoid flash)
   ```html
   <script>
       // In <head>, before body
       const saved = localStorage.getItem('themeData');
       if (saved) applyTheme(JSON.parse(saved));
   </script>
   ```

4. **Provide theme reset**
   ```javascript
   function resetToDefault() {
       localStorage.removeItem('selectedTheme');
       location.reload();
   }
   ```

---

## Examples in the Wild

See these projects using CameronPAD themes:

- **CameronPAD** (obviously!) - Full implementation
- Coming soon: Community examples

---

## Support

**Questions?** Open an issue on GitHub:
https://github.com/camayuki/cameronpad-themes/issues

**Want to contribute?** PRs welcome!

---

## License

All themes in the marketplace are MIT licensed - free to use in any project (commercial or personal)!

---

🎨 **Happy theming!**
