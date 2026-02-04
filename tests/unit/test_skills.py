"""
Unit tests for the skills state management system.

Run with: pytest tests/unit/test_skills.py -v
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from model.skills import SkillState, ExperienceTable, SkillsManager


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singletons before each test to ensure isolation."""
    ExperienceTable._instance = None
    SkillsManager.reset_instance()
    yield
    ExperienceTable._instance = None
    SkillsManager.reset_instance()


class TestSkillState:
    """Test SkillState dataclass."""

    def test_creation_with_defaults(self):
        """Test creating SkillState with default values."""
        skill = SkillState(level=50)
        assert skill.level == 50
        assert skill.xp == 0
        assert skill.xp_gained == 0
        assert isinstance(skill.timestamp, datetime)

    def test_creation_with_all_values(self):
        """Test creating SkillState with all values."""
        timestamp = datetime.now()
        skill = SkillState(level=75, xp=1210421, xp_gained=5000, timestamp=timestamp)
        assert skill.level == 75
        assert skill.xp == 1210421
        assert skill.xp_gained == 5000
        assert skill.timestamp == timestamp

    def test_has_xp_data_false_when_zero(self):
        """Test has_xp_data returns False when XP is 0."""
        skill = SkillState(level=50, xp=0)
        assert skill.has_xp_data() is False

    def test_has_xp_data_true_when_nonzero(self):
        """Test has_xp_data returns True when XP > 0."""
        skill = SkillState(level=50, xp=101333)
        assert skill.has_xp_data() is True

    def test_update_timestamp(self):
        """Test updating timestamp."""
        old_time = datetime.now() - timedelta(seconds=10)
        skill = SkillState(level=50, timestamp=old_time)

        skill.update_timestamp()

        assert skill.timestamp > old_time
        assert (datetime.now() - skill.timestamp).total_seconds() < 1


class TestExperienceTable:
    """Test ExperienceTable singleton."""

    def test_singleton_pattern(self):
        """Test that ExperienceTable is a singleton."""
        table1 = ExperienceTable()
        table2 = ExperienceTable()
        table3 = ExperienceTable.get_instance()

        assert table1 is table2
        assert table2 is table3

    def test_level_to_xp_boundaries(self):
        """Test XP thresholds for boundary levels."""
        table = ExperienceTable()

        # Level 1
        assert table.level_to_xp(1) == 0

        # Level 50
        assert table.level_to_xp(50) == 101333

        # Level 99
        assert table.level_to_xp(99) == 13034431

    def test_level_to_xp_invalid_level(self):
        """Test that invalid levels raise ValueError."""
        table = ExperienceTable()

        with pytest.raises(ValueError, match="must be between 1 and 99"):
            table.level_to_xp(0)

        with pytest.raises(ValueError, match="must be between 1 and 99"):
            table.level_to_xp(100)

    def test_xp_to_level_boundaries(self):
        """Test level calculation from XP."""
        table = ExperienceTable()

        # Exactly at thresholds
        assert table.xp_to_level(0) == 1
        assert table.xp_to_level(83) == 2
        assert table.xp_to_level(101333) == 50
        assert table.xp_to_level(13034431) == 99

    def test_xp_to_level_between_thresholds(self):
        """Test level calculation for XP between thresholds."""
        table = ExperienceTable()

        # Between level 2 and 3 (83-174)
        assert table.xp_to_level(100) == 2

        # Between level 50 and 51 (101333-111945)
        assert table.xp_to_level(105000) == 50

    def test_xp_to_level_negative_xp(self):
        """Test negative XP defaults to level 1."""
        table = ExperienceTable()
        assert table.xp_to_level(-100) == 1

    def test_xp_to_level_beyond_99(self):
        """Test XP beyond level 99 caps at 99."""
        table = ExperienceTable()
        assert table.xp_to_level(20000000) == 99

    def test_xp_to_next_level(self):
        """Test calculating next level XP threshold."""
        table = ExperienceTable()

        # Level 1 -> 2
        assert table.xp_to_next_level(0) == 83

        # Level 50 -> 51
        assert table.xp_to_next_level(101333) == 111945

        # Between levels
        assert table.xp_to_next_level(105000) == 111945

    def test_xp_to_next_level_at_99(self):
        """Test next level XP when already at 99."""
        table = ExperienceTable()

        # At level 99
        assert table.xp_to_next_level(13034431) == 13034431

        # Beyond level 99
        assert table.xp_to_next_level(20000000) == 13034431

    def test_progress_to_next_level(self):
        """Test progress percentage calculation."""
        table = ExperienceTable()

        # Exactly at level threshold (0% progress)
        assert table.progress_to_next_level(101333) == 0.0

        # Halfway between level 50 and 51
        halfway_xp = 101333 + (111945 - 101333) // 2
        progress = table.progress_to_next_level(halfway_xp)
        assert 0.49 < progress < 0.51  # Approximately 50%

        # Almost at next level
        almost_next = 111944
        progress = table.progress_to_next_level(almost_next)
        assert progress > 0.99

    def test_progress_to_next_level_at_99(self):
        """Test progress when at level 99 (should be 100%)."""
        table = ExperienceTable()

        assert table.progress_to_next_level(13034431) == 1.0
        assert table.progress_to_next_level(20000000) == 1.0

    def test_progress_to_next_level_at_1(self):
        """Test progress at level 1."""
        table = ExperienceTable()

        # 0 XP = 0% progress
        assert table.progress_to_next_level(0) == 0.0

        # Halfway to level 2 (83 XP needed)
        assert 0.45 < table.progress_to_next_level(40) < 0.55


class TestSkillsManager:
    """Test SkillsManager singleton."""

    def test_singleton_pattern(self):
        """Test that SkillsManager is a singleton."""
        manager1 = SkillsManager()
        manager2 = SkillsManager()
        manager3 = SkillsManager.get_instance()

        assert manager1 is manager2
        assert manager2 is manager3

    def test_initialization_creates_all_skills(self):
        """Test that all 24 skills are initialized."""
        manager = SkillsManager()
        all_skills = manager.get_all_skills()

        assert len(all_skills) == 24

        # Check a few key skills exist
        assert "fishing" in all_skills
        assert "woodcutting" in all_skills
        assert "magic" in all_skills

    def test_initial_skill_state(self):
        """Test that skills start at level -1 (unread) with no XP."""
        manager = SkillsManager()
        skill = manager.get_skill("fishing")

        assert skill.level == -1
        assert skill.xp == 0
        assert skill.xp_gained == 0
        assert not skill.has_xp_data()

    def test_get_skill_case_insensitive(self):
        """Test that skill names are case-insensitive."""
        manager = SkillsManager()

        skill1 = manager.get_skill("Fishing")
        skill2 = manager.get_skill("fishing")
        skill3 = manager.get_skill("FISHING")

        assert skill1 is skill2
        assert skill2 is skill3

    def test_get_skill_invalid_name(self):
        """Test that invalid skill names raise ValueError."""
        manager = SkillsManager()

        with pytest.raises(ValueError, match="Unknown skill"):
            manager.get_skill("invalidskill")

    def test_update_skill_level(self):
        """Test updating skill level via OCR."""
        manager = SkillsManager()

        manager.update_skill_level("fishing", 50)
        skill = manager.get_skill("fishing")

        assert skill.level == 50
        assert skill.xp == 101333  # Estimated XP for level 50

    def test_update_skill_level_invalid_range(self):
        """Test that invalid levels raise ValueError."""
        manager = SkillsManager()

        # Level 0 is invalid
        with pytest.raises(ValueError, match="must be -1 or between 1 and 99"):
            manager.update_skill_level("fishing", 0)

        # Level 100 is invalid
        with pytest.raises(ValueError, match="must be -1 or between 1 and 99"):
            manager.update_skill_level("fishing", 100)

        # Level -2 is invalid
        with pytest.raises(ValueError, match="must be -1 or between 1 and 99"):
            manager.update_skill_level("fishing", -2)

        # Level -1 is valid (unread)
        manager.update_skill_level("fishing", -1)
        assert manager.get_skill("fishing").level == -1

    def test_update_skill_level_notifies_observers(self):
        """Test that updating level notifies observers."""
        manager = SkillsManager()
        observer = Mock()
        manager.add_observer(observer)

        manager.update_skill_level("fishing", 50)

        observer.assert_called_once()

    def test_update_skill_level_no_notify_if_unchanged(self):
        """Test that updating to same level doesn't notify."""
        manager = SkillsManager()
        observer = Mock()

        manager.update_skill_level("fishing", 50)
        manager.add_observer(observer)
        manager.update_skill_level("fishing", 50)

        observer.assert_not_called()

    def test_update_skill_xp(self):
        """Test updating skill XP."""
        manager = SkillsManager()

        manager.update_skill_xp("fishing", 105000)
        skill = manager.get_skill("fishing")

        assert skill.xp == 105000
        assert skill.level == 50  # Auto-calculated from XP
        assert skill.has_xp_data()

    def test_update_skill_xp_calculates_gained(self):
        """Test that XP gained is auto-calculated."""
        manager = SkillsManager()

        # First update
        manager.update_skill_xp("fishing", 100000)
        skill = manager.get_skill("fishing")
        assert skill.xp_gained == 0  # No previous XP data

        # Second update
        manager.update_skill_xp("fishing", 105000)
        skill = manager.get_skill("fishing")
        assert skill.xp_gained == 5000  # 105000 - 100000

    def test_update_skill_xp_with_explicit_gained(self):
        """Test updating XP with explicit xp_gained value."""
        manager = SkillsManager()

        manager.update_skill_xp("fishing", 105000, xp_gained=1500)
        skill = manager.get_skill("fishing")

        assert skill.xp == 105000
        assert skill.xp_gained == 1500

    def test_update_skill_xp_negative_raises_error(self):
        """Test that negative XP raises ValueError."""
        manager = SkillsManager()

        with pytest.raises(ValueError, match="cannot be negative"):
            manager.update_skill_xp("fishing", -100)

    def test_update_skill_xp_notifies_observers(self):
        """Test that updating XP notifies observers."""
        manager = SkillsManager()
        observer = Mock()
        manager.add_observer(observer)

        manager.update_skill_xp("fishing", 105000)

        observer.assert_called_once()

    def test_update_skill_xp_no_notify_if_unchanged(self):
        """Test that updating to same XP doesn't notify."""
        manager = SkillsManager()
        observer = Mock()

        manager.update_skill_xp("fishing", 105000)
        manager.add_observer(observer)
        manager.update_skill_xp("fishing", 105000)

        observer.assert_not_called()

    def test_observer_add_and_remove(self):
        """Test adding and removing observers."""
        manager = SkillsManager()
        observer1 = Mock()
        observer2 = Mock()

        manager.add_observer(observer1)
        manager.add_observer(observer2)
        manager.update_skill_level("fishing", 50)

        assert observer1.call_count == 1
        assert observer2.call_count == 1

        manager.remove_observer(observer1)
        manager.update_skill_level("fishing", 51)

        assert observer1.call_count == 1  # Not called again
        assert observer2.call_count == 2  # Called again

    def test_observer_errors_dont_crash(self):
        """Test that observer errors don't crash the manager."""
        manager = SkillsManager()

        def bad_observer():
            raise RuntimeError("Observer error")

        good_observer = Mock()

        manager.add_observer(bad_observer)
        manager.add_observer(good_observer)

        # Should not raise, good observer should still be called
        manager.update_skill_level("fishing", 50)
        good_observer.assert_called_once()

    def test_get_all_skills_returns_copy(self):
        """Test that get_all_skills returns independent dict."""
        manager = SkillsManager()

        skills1 = manager.get_all_skills()
        skills2 = manager.get_all_skills()

        # Should be equal but not the same object
        assert skills1 == skills2
        assert skills1 is not skills2


class TestIntegration:
    """Integration tests for the complete system."""

    def test_ocr_then_xp_tracking_workflow(self):
        """Test typical workflow: OCR level, then track XP gains."""
        manager = SkillsManager()

        # Step 1: OCR detects level 50 fishing
        manager.update_skill_level("fishing", 50)
        skill = manager.get_skill("fishing")
        assert skill.level == 50
        assert skill.xp == 101333  # Estimated from level

        # Step 2: XP watcher detects actual XP
        manager.update_skill_xp("fishing", 105000)
        skill = manager.get_skill("fishing")
        assert skill.level == 50
        assert skill.xp == 105000
        assert skill.xp_gained == 3667  # 105000 - 101333

        # Step 3: More XP gained
        manager.update_skill_xp("fishing", 106000)
        skill = manager.get_skill("fishing")
        assert skill.xp == 106000
        assert skill.xp_gained == 4667  # Total gained

    def test_level_up_via_xp_tracking(self):
        """Test level-up detection via XP tracking."""
        manager = SkillsManager()
        table = ExperienceTable()

        # Start at level 50
        manager.update_skill_xp("fishing", 105000)
        assert manager.get_skill("fishing").level == 50

        # Gain XP to reach level 51 (111945 XP)
        manager.update_skill_xp("fishing", 112000)
        skill = manager.get_skill("fishing")
        assert skill.level == 51
        assert skill.xp == 112000

        # Check progress to level 52
        progress = table.progress_to_next_level(112000)
        assert 0.0 < progress < 0.1  # Just barely into level 51

    def test_multiple_skills_independent(self):
        """Test that multiple skills track independently."""
        manager = SkillsManager()

        manager.update_skill_xp("fishing", 105000)
        manager.update_skill_xp("woodcutting", 200000)
        manager.update_skill_level("mining", 75)

        assert manager.get_skill("fishing").xp == 105000
        assert manager.get_skill("woodcutting").xp == 200000
        assert manager.get_skill("mining").level == 75
        assert manager.get_skill("cooking").level == -1  # Unchanged (still unread)
