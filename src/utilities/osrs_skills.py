"""
OSRS skill ordering and lookup helpers.
"""
from typing import Dict, List

SKILL_ORDER: List[str] = [
    "attack",
    "hitpoints",
    "mining",
    "strength",
    "agility",
    "smithing",
    "defence",
    "herblore",
    "fishing",
    "ranged",
    "thieving",
    "cooking",
    "prayer",
    "crafting",
    "firemaking",
    "magic",
    "fletching",
    "woodcutting",
    "runecrafting",
    "slayer",
    "farming",
    "construction",
    "hunter",
    "sailing",
]

_ALIASES: Dict[str, str] = {
    "hp": "hitpoints",
    "hitpoint": "hitpoints",
    "hitpoints": "hitpoints",
    "defense": "defence",
    "range": "ranged",
    "ranged": "ranged",
    "runecraft": "runecrafting",
    "runecrafting": "runecrafting",
}

_SKILL_INDEX = {name: idx for idx, name in enumerate(SKILL_ORDER)}


def normalize_skill_name(name: str) -> str:
    """Normalize a skill name for lookup."""
    return name.strip().lower().replace(" ", "").replace("-", "")


def resolve_skill_name(name: str) -> str:
    """Resolve aliases and normalized names to a canonical skill name."""
    normalized = normalize_skill_name(name)
    return _ALIASES.get(normalized, normalized)


def skill_index(name: str) -> int:
    """Return the index of a skill in SKILL_ORDER."""
    canonical = resolve_skill_name(name)
    if canonical not in _SKILL_INDEX:
        raise ValueError(f"Unknown skill '{name}'. Valid skills: {', '.join(SKILL_ORDER)}")
    return _SKILL_INDEX[canonical]


def skill_names() -> List[str]:
    """Return the canonical skill ordering."""
    return list(SKILL_ORDER)
