#!/usr/bin/env python3
"""
Test script to verify background watchers are working.

This script will show:
1. When watchers start
2. When they detect changes (action/XP)
3. When they stop

Run the crafting bot and watch the console output to see watcher activity.
"""

import time
from model.bot_session_state import BotSessionState
from model.skills import SkillsManager


def monitor_watchers(duration_seconds=60):
    """
    Monitor watcher state for a specified duration.

    Args:
        duration_seconds: How long to monitor (default 60 seconds)
    """
    print(f"\n{'=' * 60}")
    print("WATCHER MONITOR - Watching for {duration_seconds} seconds")
    print(f"{'=' * 60}\n")

    state = BotSessionState()
    skills = SkillsManager()

    start_time = time.time()
    last_action = None
    last_xp = {}

    print("Monitoring started. Waiting for watcher updates...")
    print("(Run the crafting bot in another window to see activity)\n")

    while time.time() - start_time < duration_seconds:
        # Check for action changes
        current_action = state.get_current_action()
        if current_action != last_action:
            print(
                f"[{time.strftime('%H:%M:%S')}] ACTION CHANGE: {last_action} → {current_action}"
            )
            last_action = current_action

        # Check for XP changes
        for skill_name in ["Crafting", "Fletching", "Woodcutting"]:
            skill = skills.get_skill(skill_name)
            prev_xp = last_xp.get(skill_name, skill.xp)

            if skill.xp != prev_xp:
                gained = skill.xp - prev_xp
                print(
                    f"[{time.strftime('%H:%M:%S')}] XP CHANGE: {skill_name} +{gained} XP (total: {skill.xp})"
                )
                last_xp[skill_name] = skill.xp

        time.sleep(0.5)

    print(f"\n{'=' * 60}")
    print("Monitoring complete")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    print("Background Watcher Test Script")
    print("===============================")
    print("\nThis script monitors the BotSessionState and SkillsManager")
    print("to show when background watchers update the state.\n")
    print("Instructions:")
    print("1. Run this script")
    print("2. In another window, start the crafting bot")
    print("3. Watch this console for watcher activity\n")

    input("Press Enter to start monitoring...")

    try:
        monitor_watchers(duration_seconds=120)  # Monitor for 2 minutes
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
