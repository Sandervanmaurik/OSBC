"""
BehaviorHelpersMixin - Context-aware behavior helpers for OSRS mixins.

Provides semantic behavior methods that mixins can call instead of raw
behavior.timing.sleep() calls. Centralizes behavior logic and provides
context-appropriate delays.

This keeps behavior patterns DRY and gives meaningful names to delays
instead of magic numbers scattered through mixin code.
"""

from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Tuple

import utilities.random_util as rd

if TYPE_CHECKING:
    from utilities.behavior import BehaviorManager


class BehaviorHelpersMixin:
    """
    Mixin providing context-aware behavior helpers.

    Mixins should use these methods instead of raw self.behavior calls.
    This keeps behavior logic DRY and provides semantic meaning.

    Usage in BankingMixin:
        self.banking_hesitation()  # Not: self.behavior.timing.sleep((0.2, 0.6))

    Usage in ItemInteractionMixin:
        with self.with_paused_fidgeting():
            self.click_inventory_slot(slot)
    """

    if TYPE_CHECKING:
        behavior: "BehaviorManager"

    # ===== Banking Context =====

    def banking_hesitation(self) -> None:
        """
        Add hesitation before opening bank or interacting with bank UI.
        Simulates human "thinking" before banking.
        """
        if self.behavior.action.should_hesitate():
            self.behavior.timing.sleep((0.3, 0.8))

    def banking_click_delay(self) -> None:
        """
        Delay after clicking a bank element (booth, slot, etc.).
        Short delay to simulate human reaction time.
        """
        self.behavior.timing.sleep((0.15, 0.35))

    def banking_deposit_delay(self) -> None:
        """
        Delay between depositing multiple item types.
        Slightly shorter than general click delay for repetitive actions.
        """
        self.behavior.timing.sleep((0.15, 0.3))

    def banking_wait_open_poll(self) -> None:
        """
        Polling delay while waiting for bank to open.
        Frequent checks with short delays for responsiveness.
        """
        self.behavior.timing.sleep((0.12, 0.25))

    def banking_post_deposit_delay(self) -> None:
        """
        Delay after completing deposit sequence.
        Gives time for UI to update before next action.
        """
        self.behavior.timing.sleep((0.3, 0.7))

    # ===== Item Interaction Context =====

    def interaction_pre_click_delay(self) -> None:
        """
        Tiny delay before clicking an inventory slot.
        Simulates visual targeting time.
        """
        self.behavior.timing.sleep((0.02, 0.06))

    def interaction_between_clicks_delay(self) -> None:
        """
        Micro-delay between consecutive item clicks.
        Very short for fluid item-on-item actions.
        """
        self.behavior.timing.sleep((0.03, 0.08))

    def interaction_post_action_delay(self) -> None:
        """
        Delay after completing an item interaction sequence.
        Brief pause before next action.
        """
        self.behavior.timing.sleep((0.03, 0.08))

    def interaction_space_confirm_delay(
        self, delay_range: Tuple[float, float] = (0.5, 1.5)
    ) -> float:
        """
        Calculate delay before pressing space to confirm.

        Args:
            delay_range: (min, max) delay range in seconds

        Returns:
            Actual delay used (for logging/debugging)
        """
        min_delay, max_delay = delay_range
        mean_delay = (min_delay + max_delay) / 2
        std_delay = (max_delay - min_delay) / 4

        delay = rd.truncated_normal_sample(
            min_delay, max_delay, mean=mean_delay, std=std_delay
        )
        self.behavior.timing.sleep((delay, delay))
        return delay

    # ===== Action Waiting Context =====

    def action_poll_delay(self) -> None:
        """
        Polling delay while waiting for action to start.
        Frequent checks with short delays.
        """
        self.behavior.timing.sleep((0.08, 0.18))

    def action_progress_poll_delay(self) -> None:
        """
        Polling delay while action is in progress.
        Longer delays since action completion is gradual.
        """
        self.behavior.timing.sleep((0.2, 0.6))

    # ===== Camera/Search Context =====

    def search_rotation_delay(self) -> None:
        """
        Delay after rotating camera during search.
        Gives time for camera to settle and objects to render.
        """
        self.behavior.timing.sleep((0.5, 1.2))

    # ===== Fidgeting Helpers =====

    @contextmanager
    def with_paused_fidgeting(self) -> Iterator[None]:
        """
        Context manager that pauses fidgeting during critical actions.

        Prevents mouse fidgeting from interfering with precise actions
        like clicking inventory slots or using items on each other.

        Usage:
            with self.with_paused_fidgeting():
                self.click_inventory_slot(slot_index)
                self.click_inventory_slot(other_slot)
        """
        self.behavior.pause_fidgeting()
        try:
            yield
        finally:
            self.behavior.resume_fidgeting()

    # ===== Misclick Simulation =====

    def maybe_banking_misclick(self, target_point) -> None:
        """
        Possibly simulate a misclick during banking.
        Banking has lower misclick chance (more focused task).

        Args:
            target_point: The intended click target
        """
        if self.behavior.action.should_misclick(chance_override=0.03):
            self.behavior.action.execute_misclick(target_point)

    def maybe_interaction_misclick(self, target_point) -> None:
        """
        Possibly simulate a misclick during item interaction.
        Uses default misclick chance from config.

        Args:
            target_point: The intended click target
        """
        if self.behavior.action.should_misclick():
            self.behavior.action.execute_misclick(target_point)
