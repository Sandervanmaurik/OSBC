"""
Data models for Script Chains.

Defines the structure for chains of bot scripts that execute sequentially.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import json
from pathlib import Path


class ChainEntryStatus(Enum):
    """Status of a script entry in the chain."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"  # When items are missing after retry
    FAILED = "failed"


@dataclass
class ChainEntry:
    """
    A single script in a chain.

    Attributes:
        script_name: Bot class name (e.g., "OSRSFishing")
        running_time: Duration in minutes
        options: Bot-specific configuration options
        order: Position in chain (0-indexed)
        status: Current execution status
        xp_gained: XP accumulated during execution
    """

    script_name: str
    running_time: int
    options: Dict[str, Any] = field(default_factory=dict)
    order: int = 0
    status: ChainEntryStatus = ChainEntryStatus.PENDING
    xp_gained: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "script_name": self.script_name,
            "running_time": self.running_time,
            "options": self.options,
            "order": self.order,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ChainEntry":
        """Create ChainEntry from dictionary."""
        return ChainEntry(
            script_name=data["script_name"],
            running_time=data["running_time"],
            options=data.get("options", {}),
            order=data.get("order", 0),
        )


@dataclass
class ScriptChain:
    """
    A named sequence of bot scripts.

    Attributes:
        name: User-defined name for the chain
        entries: List of scripts to execute in order
        created_at: ISO timestamp of creation
        updated_at: ISO timestamp of last update
    """

    name: str
    entries: List[ChainEntry] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()

    def add_entry(self, entry: ChainEntry) -> None:
        """Add a script entry to the chain."""
        entry.order = len(self.entries)
        self.entries.append(entry)
        self.updated_at = datetime.now().isoformat()

    def remove_entry(self, index: int) -> None:
        """Remove a script entry at the given index."""
        if 0 <= index < len(self.entries):
            self.entries.pop(index)
            # Re-number remaining entries
            for i, entry in enumerate(self.entries):
                entry.order = i
            self.updated_at = datetime.now().isoformat()

    def reorder(self, from_idx: int, to_idx: int) -> None:
        """Move an entry from one position to another."""
        if 0 <= from_idx < len(self.entries) and 0 <= to_idx < len(self.entries):
            entry = self.entries.pop(from_idx)
            self.entries.insert(to_idx, entry)
            # Re-number all entries
            for i, e in enumerate(self.entries):
                e.order = i
            self.updated_at = datetime.now().isoformat()

    def total_time_minutes(self) -> int:
        """Calculate total expected duration in minutes."""
        return sum(e.running_time for e in self.entries)

    def reset_status(self) -> None:
        """Reset all entry statuses to PENDING before execution."""
        for entry in self.entries:
            entry.status = ChainEntryStatus.PENDING
            entry.xp_gained = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "entries": [e.to_dict() for e in self.entries],
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ScriptChain":
        """Create ScriptChain from dictionary."""
        return ScriptChain(
            name=data["name"],
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            entries=[ChainEntry.from_dict(e) for e in data.get("entries", [])],
        )


# Storage configuration
CHAINS_DIR = Path(__file__).parent.parent.parent / "data"
CHAINS_FILE = CHAINS_DIR / "chains.json"


def save_chains(chains: Dict[str, ScriptChain]) -> None:
    """
    Save all chains to JSON file.

    Args:
        chains: Dictionary mapping chain name to ScriptChain
    """
    # Ensure data directory exists
    CHAINS_DIR.mkdir(parents=True, exist_ok=True)

    # Convert chains to JSON format
    data = {name: chain.to_dict() for name, chain in chains.items()}

    # Write to file
    CHAINS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_chains() -> Dict[str, ScriptChain]:
    """
    Load all chains from JSON file.

    Returns:
        Dictionary mapping chain name to ScriptChain
    """
    if not CHAINS_FILE.exists():
        return {}

    try:
        data = json.loads(CHAINS_FILE.read_text(encoding="utf-8"))
        return {
            name: ScriptChain.from_dict(chain_data) for name, chain_data in data.items()
        }
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error loading chains: {e}")
        return {}


def delete_chain(chain_name: str) -> bool:
    """
    Delete a chain by name.

    Args:
        chain_name: Name of the chain to delete

    Returns:
        True if chain was found and deleted, False otherwise
    """
    chains = load_chains()
    if chain_name in chains:
        del chains[chain_name]
        save_chains(chains)
        return True
    return False
