"""
Unit tests for the behavior system.

Run with: pytest tests/unit/test_behavior_system.py
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch

from utilities.behavior import BehaviorManager, BehaviorProfiles
from utilities.behavior.modules import (
    TimingBehavior,
    MouseBehavior,
    ActionBehavior,
    AttentionBehavior,
    BreakBehavior,
)
from utilities.geometry import Point


@pytest.fixture
def mock_bot():
    """Create a mock bot for testing."""
    bot = Mock()
    bot.mouse = Mock()
    bot.win = Mock()
    bot.win.game_view = Mock()
    bot.win.game_view.random_point.return_value = Point(100, 100)
    bot.win.cp_tabs = [Mock() for _ in range(11)]
    bot.win.inventory_slots = [Mock() for _ in range(28)]
    bot.move_camera = Mock()
    bot.log_msg = Mock()
    return bot


class TestBehaviorProfiles:
    """Test behavior profiles."""

    def test_get_valid_profile(self):
        """Test getting valid profiles."""
        cautious = BehaviorProfiles.get("cautious")
        assert cautious["name"] == "Cautious"
        assert "timing" in cautious
        assert "mouse" in cautious

        experienced = BehaviorProfiles.get("experienced")
        assert experienced["name"] == "Experienced"

        focused = BehaviorProfiles.get("focused")
        assert focused["name"] == "Focused"

    def test_get_invalid_profile(self):
        """Test getting invalid profile raises error."""
        with pytest.raises(ValueError):
            BehaviorProfiles.get("invalid")

    def test_list_profiles(self):
        """Test listing available profiles."""
        profiles = BehaviorProfiles.list_profiles()
        assert "cautious" in profiles
        assert "experienced" in profiles
        assert "focused" in profiles

    def test_get_profile_description(self):
        """Test getting profile descriptions."""
        desc = BehaviorProfiles.get_profile_description("experienced")
        assert isinstance(desc, str)
        assert len(desc) > 0


class TestTimingBehavior:
    """Test timing behavior module."""

    def test_initialization(self, mock_bot):
        """Test timing behavior initialization."""
        config = {"speed_multiplier": 1.5}
        timing = TimingBehavior(config, mock_bot)

        assert timing.bot == mock_bot
        assert timing.enabled is True
        assert timing.config["speed_multiplier"] == 1.5

    def test_sleep_with_preset(self, mock_bot):
        """Test sleep with preset duration."""
        timing = TimingBehavior({}, mock_bot)

        start = time.time()
        timing.sleep("very_fast")
        elapsed = time.time() - start

        # Should be in range of very_fast preset (0.02-0.08s)
        assert 0.01 <= elapsed <= 0.15  # Allow some margin

    def test_sleep_with_tuple(self, mock_bot):
        """Test sleep with custom tuple range."""
        timing = TimingBehavior({}, mock_bot)

        start = time.time()
        timing.sleep((0.1, 0.2))
        elapsed = time.time() - start

        assert 0.05 <= elapsed <= 0.25  # Allow margin

    def test_sleep_with_fixed(self, mock_bot):
        """Test sleep with fixed duration."""
        timing = TimingBehavior({}, mock_bot)

        start = time.time()
        timing.sleep(0.1)
        elapsed = time.time() - start

        assert abs(elapsed - 0.1) < 0.05  # Should be very close to 0.1

    def test_sleep_with_speed_multiplier(self, mock_bot):
        """Test that speed multiplier affects sleep duration."""
        timing = TimingBehavior({"speed_multiplier": 2.0}, mock_bot)

        start = time.time()
        timing.sleep((0.1, 0.1))  # Fixed range
        elapsed = time.time() - start

        # With 2x multiplier, should take ~0.2s
        assert 0.15 <= elapsed <= 0.25

    def test_sleep_disabled(self, mock_bot):
        """Test that sleep does nothing when disabled."""
        timing = TimingBehavior({}, mock_bot)
        timing.disable()

        start = time.time()
        result = timing.sleep("long")
        elapsed = time.time() - start

        assert result == 0.0
        assert elapsed < 0.01  # Should return immediately

    def test_reaction_delay(self, mock_bot):
        """Test reaction delay."""
        timing = TimingBehavior({}, mock_bot)

        start = time.time()
        timing.reaction_delay()
        elapsed = time.time() - start

        # Should be in default reaction range (0.15-0.45s)
        assert 0.1 <= elapsed <= 0.5

    def test_invalid_preset(self, mock_bot):
        """Test invalid preset raises error."""
        timing = TimingBehavior({}, mock_bot)

        with pytest.raises(ValueError):
            timing.sleep("invalid_preset")


class TestMouseBehavior:
    """Test mouse behavior module."""

    def test_initialization(self, mock_bot):
        """Test mouse behavior initialization."""
        config = {"default_speed": "slow"}
        mouse = MouseBehavior(config, mock_bot)

        assert mouse.bot == mock_bot
        assert mouse.config["default_speed"] == "slow"

    def test_move_to_with_point(self, mock_bot):
        """Test move_to with Point object."""
        mouse = MouseBehavior({}, mock_bot)
        target = Point(100, 200)

        mouse.move_to(target)

        mock_bot.mouse.move_to.assert_called_once()
        args, kwargs = mock_bot.mouse.move_to.call_args
        assert args[0] == (100, 200)

    def test_move_to_with_tuple(self, mock_bot):
        """Test move_to with tuple."""
        mouse = MouseBehavior({}, mock_bot)

        mouse.move_to((100, 200))

        mock_bot.mouse.move_to.assert_called_once()
        args = mock_bot.mouse.move_to.call_args[0]
        assert args[0] == (100, 200)

    def test_move_to_with_speed_override(self, mock_bot):
        """Test move_to with speed override."""
        mouse = MouseBehavior({"default_speed": "fast"}, mock_bot)

        mouse.move_to((100, 200), mouseSpeed="slow")

        _, kwargs = mock_bot.mouse.move_to.call_args
        assert kwargs["mouseSpeed"] == "slow"

    def test_click(self, mock_bot):
        """Test click method."""
        mouse = MouseBehavior({}, mock_bot)

        mouse.click()
        mock_bot.mouse.click.assert_called_once_with(button="left", force_delay=False)

    def test_right_click(self, mock_bot):
        """Test right click method."""
        mouse = MouseBehavior({}, mock_bot)

        mouse.right_click()
        mock_bot.mouse.right_click.assert_called_once()


class TestActionBehavior:
    """Test action behavior module."""

    def test_should_misclick(self, mock_bot):
        """Test misclick probability."""
        action = ActionBehavior({"misclick_chance": 1.0}, mock_bot)
        assert action.should_misclick() is True

        action = ActionBehavior({"misclick_chance": 0.0}, mock_bot)
        assert action.should_misclick() is False

    def test_should_hesitate(self, mock_bot):
        """Test hesitation probability."""
        action = ActionBehavior({"hesitation_chance": 1.0}, mock_bot)
        assert action.should_hesitate() is True

        action = ActionBehavior({"hesitation_chance": 0.0}, mock_bot)
        assert action.should_hesitate() is False

    def test_execute_misclick(self, mock_bot):
        """Test misclick execution."""
        # Setup mock behavior manager
        mock_bot.behavior = Mock()
        mock_bot.behavior.mouse = Mock()
        mock_bot.behavior.timing = Mock()

        action = ActionBehavior({}, mock_bot)
        target = Point(100, 100)

        action.execute_misclick(target, correct_after=False)

        # Should have moved and clicked once
        mock_bot.behavior.mouse.move_to.assert_called_once()
        mock_bot.behavior.mouse.click.assert_called_once()


class TestAttentionBehavior:
    """Test attention behavior module."""

    def test_initialization(self, mock_bot):
        """Test attention behavior initialization."""
        attention = AttentionBehavior({}, mock_bot)

        assert hasattr(attention, "_last_camera_move")
        assert hasattr(attention, "_camera_interval")

    def test_camera_disabled(self, mock_bot):
        """Test camera movement when disabled."""
        attention = AttentionBehavior({"camera_enabled": False}, mock_bot)

        attention.random_camera_movement()

        # Should not call move_camera
        mock_bot.move_camera.assert_not_called()

    def test_camera_enabled(self, mock_bot):
        """Test camera movement when enabled."""
        mock_bot.behavior = Mock()
        mock_bot.behavior.timing = Mock()
        mock_bot.behavior.timing.sleep = Mock()

        attention = AttentionBehavior({"camera_enabled": True}, mock_bot)

        attention.random_camera_movement()

        # Should call move_camera
        mock_bot.move_camera.assert_called_once()


class TestBreakBehavior:
    """Test break behavior module."""

    def test_should_take_break_disabled(self, mock_bot):
        """Test break check when disabled."""
        breaks = BreakBehavior({"enabled": False}, mock_bot)
        assert breaks.should_take_break() is False

    def test_should_take_break_enabled(self, mock_bot):
        """Test break check when enabled."""
        # 100% chance
        breaks = BreakBehavior({"enabled": True, "chance_per_check": 1.0}, mock_bot)
        assert breaks.should_take_break() is True

        # 0% chance
        breaks = BreakBehavior({"enabled": True, "chance_per_check": 0.0}, mock_bot)
        assert breaks.should_take_break() is False

    @patch("time.sleep")
    def test_take_break(self, mock_sleep, mock_bot):
        """Test taking a break."""
        breaks = BreakBehavior({"duration_min": 1.0, "duration_max": 1.0}, mock_bot)

        duration = breaks.take_break()

        assert duration >= 1.0
        mock_bot.log_msg.assert_called()


class TestBehaviorManager:
    """Test behavior manager."""

    def test_initialization(self, mock_bot):
        """Test manager initialization."""
        manager = BehaviorManager(mock_bot, profile="experienced")

        assert manager.bot == mock_bot
        assert manager.profile_name == "experienced"
        assert hasattr(manager, "timing")
        assert hasattr(manager, "mouse")
        assert hasattr(manager, "action")
        assert hasattr(manager, "attention")
        assert hasattr(manager, "breaks")

    def test_custom_config_merge(self, mock_bot):
        """Test custom config merging."""
        manager = BehaviorManager(
            mock_bot,
            profile="experienced",
            custom_config={
                "timing": {"speed_multiplier": 2.0},
                "attention": {"camera_enabled": False},
            },
        )

        assert manager.timing.config["speed_multiplier"] == 2.0
        assert manager.attention.config["camera_enabled"] is False

    def test_configure(self, mock_bot):
        """Test runtime configuration."""
        manager = BehaviorManager(mock_bot, profile="experienced")

        manager.configure(camera_enabled=False, breaks_enabled=True)

        assert manager.attention.config["camera_enabled"] is False
        assert manager.breaks.enabled is True

    def test_disable_all(self, mock_bot):
        """Test disabling all modules."""
        manager = BehaviorManager(mock_bot, profile="experienced")

        manager.disable_all()

        assert manager.timing.enabled is False
        assert manager.mouse.enabled is False
        assert manager.action.enabled is False
        assert manager.attention.enabled is False
        assert manager.breaks.enabled is False

    def test_enable_all(self, mock_bot):
        """Test enabling all modules."""
        manager = BehaviorManager(mock_bot, profile="experienced")
        manager.disable_all()

        manager.enable_all()

        assert manager.timing.enabled is True
        assert manager.mouse.enabled is True
        assert manager.action.enabled is True
        assert manager.attention.enabled is True
        assert manager.breaks.enabled is True

    def test_update_speed_multiplier(self, mock_bot):
        """Test updating speed multiplier."""
        manager = BehaviorManager(mock_bot, profile="experienced")

        manager.update_speed_multiplier(1.5)

        assert manager.timing.config["speed_multiplier"] == 1.5

    def test_summary(self, mock_bot):
        """Test configuration summary."""
        manager = BehaviorManager(mock_bot, profile="experienced")

        summary = manager.summary()

        assert isinstance(summary, str)
        assert "Experienced" in summary
        assert "Module Status" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
