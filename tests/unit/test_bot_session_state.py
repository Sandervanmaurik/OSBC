"""
Unit tests for BotSessionState XP/hour tracking.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


@pytest.fixture
def clean_state():
    """Reset BotSessionState singleton before each test."""
    from model.bot_session_state import BotSessionState

    BotSessionState.reset_instance()
    yield BotSessionState()
    BotSessionState.reset_instance()


def test_start_time_tracking(clean_state):
    """Test that reset() sets the start time."""
    clean_state.reset()
    assert clean_state._start_time is not None
    assert isinstance(clean_state._start_time, datetime)


def test_xp_per_hour_no_start_time(clean_state):
    """Test XP/hour returns 0 when no start time is set."""
    # Don't call reset() - start_time should be None
    xp_per_hour = clean_state.get_xp_per_hour()
    assert xp_per_hour == 0


@patch("model.bot_session_state.BotSessionState.get_total_xp_gained")
def test_xp_per_hour_calculation(mock_xp_gained, clean_state):
    """Test XP/hour calculation with mocked XP and time."""
    # Set up mock: 1000 XP gained
    mock_xp_gained.return_value = 1000

    # Set start time to 1 hour ago
    clean_state._start_time = datetime.now() - timedelta(hours=1)

    # Calculate XP/hour
    xp_per_hour = clean_state.get_xp_per_hour()

    # Should be approximately 1000 XP/hour (within small margin for execution time)
    assert 995 <= xp_per_hour <= 1005


@patch("model.bot_session_state.BotSessionState.get_total_xp_gained")
def test_xp_per_hour_half_hour(mock_xp_gained, clean_state):
    """Test XP/hour calculation with 30 minutes elapsed."""
    # Set up mock: 500 XP gained in 30 minutes
    mock_xp_gained.return_value = 500

    # Set start time to 30 minutes ago
    clean_state._start_time = datetime.now() - timedelta(minutes=30)

    # Calculate XP/hour
    xp_per_hour = clean_state.get_xp_per_hour()

    # Should be approximately 1000 XP/hour (500 XP in 0.5 hours)
    assert 995 <= xp_per_hour <= 1005


@patch("model.bot_session_state.BotSessionState.get_total_xp_gained")
def test_xp_per_hour_zero_xp(mock_xp_gained, clean_state):
    """Test XP/hour returns 0 when no XP gained."""
    # Set up mock: 0 XP gained
    mock_xp_gained.return_value = 0

    # Set start time to 1 hour ago
    clean_state._start_time = datetime.now() - timedelta(hours=1)

    # Calculate XP/hour
    xp_per_hour = clean_state.get_xp_per_hour()

    # Should be 0
    assert xp_per_hour == 0


@patch("model.bot_session_state.BotSessionState.get_total_xp_gained")
def test_xp_per_hour_short_duration(mock_xp_gained, clean_state):
    """Test XP/hour calculation with very short duration (seconds)."""
    # Set up mock: 100 XP gained
    mock_xp_gained.return_value = 100

    # Set start time to 10 seconds ago
    clean_state._start_time = datetime.now() - timedelta(seconds=10)

    # Calculate XP/hour
    xp_per_hour = clean_state.get_xp_per_hour()

    # 100 XP in 10 seconds = 36,000 XP/hour
    # Allow margin for execution time
    assert 35000 <= xp_per_hour <= 37000


def test_reset_clears_start_time(clean_state):
    """Test that reset() sets a new start time."""
    # First reset
    clean_state.reset()
    first_time = clean_state._start_time

    # Wait a tiny bit
    import time

    time.sleep(0.01)

    # Second reset
    clean_state.reset()
    second_time = clean_state._start_time

    # Times should be different
    assert second_time > first_time
