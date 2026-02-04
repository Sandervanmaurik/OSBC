import cv2
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utilities.imagesearch import BOT_IMAGES, search_img_in_rect

# Load the failed icon screenshot
failed_icon = cv2.imread(
    "debug_screenshots/failed_icon_20260204_174449_no_match_conf_0_00.png"
)
print(f"Failed icon shape: {failed_icon.shape}")

# Load crafting template
crafting_template_path = BOT_IMAGES / "skills" / "crafting.png"
crafting = cv2.imread(str(crafting_template_path), cv2.IMREAD_UNCHANGED)
print(f"Crafting template shape: {crafting.shape}")
print(f"Crafting template path: {crafting_template_path}")

# Try to match
print("\nTesting match with different confidence thresholds:")
for conf in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    result = search_img_in_rect(crafting, failed_icon, confidence=conf)
    print(f"  Confidence {conf}: {'MATCH' if result else 'no match'}")

# Also try the reverse (in case I have the args backwards)
print("\nTesting REVERSE (in case args are backwards):")
for conf in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    result = search_img_in_rect(failed_icon, crafting, confidence=conf)
    print(f"  Confidence {conf}: {'MATCH' if result else 'no match'}")
