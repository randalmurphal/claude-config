---
name: plasma6-panel-config
description: Configure KDE Plasma 6 panels, widgets, digital clock fonts, and Panel Colorizer styling. Use when modifying panel appearance, copying panel configs between monitors, fixing widget fonts, or troubleshooting Panel Colorizer not applying styles.
---

# Plasma 6 Panel Configuration

**Purpose:** Modify Plasma panel/widget configs without trial-and-error pain.
**When to use:** Panel styling, clock fonts, colorizer issues, multi-monitor panel sync.

---

## Critical: Edit Workflow

**Plasmashell overwrites config on exit.** Always:

```bash
pkill plasmashell
# make edits to config file
nohup plasmashell &>/dev/null &
```

---

## Config File

**Location:** `~/.config/plasma-org.kde.plasma.desktop-appletsrc`

**Format:** INI-style with nested sections. File is ~66K tokens - use grep/offset reads.

**Structure:**
```ini
[Containments][PANEL_ID]
lastScreen=SCREEN_NUMBER
plugin=org.kde.panel

[Containments][PANEL_ID][Applets][WIDGET_ID]
plugin=org.kde.plasma.digitalclock

[Containments][PANEL_ID][Applets][WIDGET_ID][Configuration][Appearance]
# widget-specific settings here
```

---

## Finding Things

| Find | Grep Pattern |
|------|-------------|
| All panels | `plugin=org.kde.panel` |
| Digital clocks | `plugin=org.kde.plasma.digitalclock` |
| Panel Colorizer | `plugin=luisbocanegra.panel.colorizer` |
| Screen mapping | `lastScreen=` |
| Appearance sections | `\[Configuration\]\[Appearance\]` |

---

## Digital Clock Font Settings

Under `[Containments][PANEL][Applets][CLOCK][Configuration][Appearance]`:

| Setting | Required Value | Notes |
|---------|---------------|-------|
| `autoFontAndSize` | `false` | **CRITICAL** - must be false or font settings ignored |
| `fontFamily` | e.g. `Hack Nerd Font` | Font name exactly as system knows it |
| `fontSize` | e.g. `9` | Integer |
| `boldText` | `true` or `false` | |
| `fontStyleName` | e.g. `Bold` | |
| `fontWeight` | e.g. `700` | 400=normal, 700=bold |

**BAD:** Adding font settings without `autoFontAndSize=false`
```ini
fontFamily=Hack Nerd Font
fontSize=9
```
**Result:** Settings silently ignored, uses system default.

**GOOD:** Include the disable flag
```ini
autoFontAndSize=false
fontFamily=Hack Nerd Font
fontSize=9
fontStyleName=Bold
fontWeight=700
boldText=true
```

---

## Panel Colorizer

### Preset Location
```
~/.local/share/plasma/plasmoids/luisbocanegra.panel.colorizer/contents/ui/presets/
```

### Config Location
Under `[Containments][PANEL][Applets][COLORIZER][Configuration][General]`:
```ini
globalSettings={"panel":{"normal":{"enabled":true,...huge JSON...}}}
lastPreset=/path/to/preset
```

### The JSON Blob

`globalSettings` is a **single-line JSON blob** (thousands of chars). Key paths:

| JSON Path | Purpose | Required for Styling |
|-----------|---------|---------------------|
| `panel.normal.enabled` | Master enable | **Must be `true`** |
| `panel.normal.backgroundColor.enabled` | Enable bg color | Yes for custom bg |
| `panel.normal.backgroundColor.custom` | Hex color | e.g. `#000000` |
| `panel.normal.backgroundColor.sourceType` | Color source | `0` = use custom |
| `widgets.normal.foregroundColor.enabled` | Enable text color | Yes for custom text |
| `widgets.normal.foregroundColor.custom` | Hex color | e.g. `#FFFFFF` |

**BAD:** Panel colorizer not styling
```json
"panel":{"normal":{"enabled":false,...
```
**Result:** All styling silently disabled.

**GOOD:** Enable the panel styling
```json
"panel":{"normal":{"enabled":true,...
```

### Copying Colorizer Between Panels

1. Find source panel's colorizer widget ID
2. Copy entire `globalSettings=` line to target
3. Copy `lastPreset=` line if using presets

---

## Randy's Current Panel Mapping

| Panel ID | Screen | Monitor | Clock Widget | Colorizer Widget |
|----------|--------|---------|--------------|------------------|
| 209 | 2 | HP | 309 | 323 |
| 273 | 0 | LG | 276 | 321 |
| 291 | 1 | ASUS | 326 | 345 |

**Note:** Widget IDs are arbitrary. Always grep for plugin names to find current IDs.

---

## Common Gotchas

| Issue | Cause | Fix |
|-------|-------|-----|
| Edits not persisting | Plasmashell overwrote on restart | Kill plasmashell BEFORE editing |
| Font settings ignored | Missing `autoFontAndSize=false` | Add the flag |
| Colorizer does nothing | `panel.normal.enabled: false` in JSON | Set to `true` |
| Wrong panel modified | Screen numbers changed | Verify `lastScreen` values |
| Can't find widget | Grepping wrong plugin name | Use exact plugin string |

---

## Quick Copy-Paste Templates

### Clock with Hack Nerd Font
```ini
[Containments][PANEL_ID][Applets][CLOCK_ID][Configuration][Appearance]
autoFontAndSize=false
boldText=true
customDateFormat=ddd, MMM d |
dateDisplayFormat=BesideTime
dateFormat=custom
fontFamily=Hack Nerd Font
fontSize=9
fontStyleName=Bold
fontWeight=700
showLocalTimezone=true
showSeconds=2
use24hFormat=2
```
