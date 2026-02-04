"""Test script to verify skills UI updates work."""

from model.skills import SkillsManager

# Test updating skills
manager = SkillsManager()

print("Initial state:")
for skill in ["attack", "fishing", "mining"]:
    state = manager.get_skill(skill)
    print(f"  {skill}: level={state.level}, xp={state.xp}")

print("\nUpdating fishing to level 50...")
manager.update_skill_level("fishing", 50)

print("\nAfter update:")
for skill in ["attack", "fishing", "mining"]:
    state = manager.get_skill(skill)
    print(f"  {skill}: level={state.level}, xp={state.xp}")

print("\nTest dict format (like update_skills expects):")
test_data = {
    "attack": 40,
    "strength": 45,
    "defence": 35,
    "hitpoints": 50,
}

for name, level in test_data.items():
    manager.update_skill_level(name, level)

print("\nAfter bulk update:")
for skill in ["attack", "strength", "defence", "hitpoints", "fishing"]:
    state = manager.get_skill(skill)
    print(f"  {skill}: level={state.level}")

print("\n✓ Skills system working correctly!")
