# Feature: Fishing Bot (Raw Shrimp)

## Objective
Automate fishing raw shrimp from light blue fishing spot tiles and drop the caught fish while keeping tools.

## Acceptance Criteria
- [ ] Detect light blue fishing spot tiles in the game view and confirm a fish icon inside the tile.
- [ ] Start fishing when a valid spot is clicked and continue until the action stops.
- [ ] Drop raw shrimp when inventory is full without dropping tools.
- [ ] Recover gracefully when spots are not found or fishing times out.

## Visual Requirements
- **Detection targets**: Light blue fishing spot outlines with raw shrimp icon inside.
- **Color requirements**: Light blue outline (cyan-like) and green bank tag reserved for future use.
- **OCR requirements**: Action text containing "Fishing" to detect active state.
- **Screenshot fixtures**: Fishing spot visible, no spot visible, inventory full with raw shrimp.

## API Integration
- **Required endpoints**: None (visual-only detection).
- **Game state dependencies**: Inventory full detection, action text detection.
- **Timing constraints**: Spot detection and hover checks under 100ms per cycle.

## Game Client Setup
- **Prerequisites**: Fishing spot tiles enabled with light blue outlines.
- **Manual setup**: Player near shrimp spot with small net in inventory.
- **Test environment**: Any shrimp fishing area with visible tile overlays.

## Edge Cases
- **Visual variations**: Different zoom levels or outline thickness.
- **Timing issues**: Action text delays after clicking spot.
- **Error conditions**: No spots found, template mismatch, inventory full without detected fish.
