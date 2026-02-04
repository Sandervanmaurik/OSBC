# XP Icon Templates

This directory contains skill icon templates extracted from OSRS XP popups.
These templates are used by the XP Watcher to automatically detect which skill gained XP.

## File Naming Convention

Icons should be named: `{skill_name}_xp_icon.png`

Examples:
- `fishing_xp_icon.png`
- `mining_xp_icon.png`
- `woodcutting_xp_icon.png`

## How to Extract Icons

1. **Gain XP in-game** for the skill you want to extract
2. **Capture the XP popup:**
   ```bash
   python scripts/manual_capture.py xp_popup_fishing
   ```
3. **Extract the skill icon:**
   ```bash
   # Interactive mode (recommended)
   python scripts/extract_xp_icons.py debug_screenshots/TIMESTAMP_xp_popup_fishing/full_client.png fishing
   
   # Or with coordinates (if you know them)
   python scripts/extract_xp_icons.py screenshot.png fishing --coords 100 50 20 20
   ```
4. **Verify extraction:**
   The icon will be saved to this directory automatically

## Template Requirements

- **Size:** Typically 16x16 to 24x24 pixels
- **Format:** PNG with transparency if possible
- **Quality:** Clear, sharp icon from XP popup
- **Background:** Preferably with the dark popup background for better matching

## Testing

After extracting icons, test the XP Watcher:

```bash
# View detection area
python scripts/test_xp_watcher.py --screenshot

# Monitor XP detection
python scripts/test_xp_watcher.py --monitor --duration 60
```

## Current Status

Icons extracted: 0/24

### Priority Skills (extract these first):
- [ ] fishing
- [ ] mining  
- [ ] woodcutting
- [ ] combat skills (attack, strength, defence, hitpoints, prayer)
- [ ] cooking
- [ ] firemaking

### All Skills:
- [ ] attack
- [ ] hitpoints
- [ ] mining
- [ ] strength
- [ ] agility
- [ ] smithing
- [ ] defence
- [ ] herblore
- [ ] fishing
- [ ] ranged
- [ ] thieving
- [ ] cooking
- [ ] prayer
- [ ] crafting
- [ ] firemaking
- [ ] magic
- [ ] fletching
- [ ] woodcutting
- [ ] runecrafting
- [ ] slayer
- [ ] farming
- [ ] construction
- [ ] hunter
- [ ] sailing (if applicable)
