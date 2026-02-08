"""
ChainSummaryDialog - Shows completion summary after chain finishes.

Displays:
    - Chain name
    - Total time elapsed
    - Scripts completed/skipped/failed breakdown
    - Total XP gained (by skill)
    - Option to run again or close
"""

import customtkinter
from typing import Dict
from model.chain import ScriptChain, ChainEntryStatus


class ChainSummaryDialog(customtkinter.CTkToplevel):
    """
    Dialog shown when a script chain completes.

    Shows completion statistics and XP gains.
    """

    def __init__(
        self, parent, chain: ScriptChain, total_xp: Dict[str, int], on_run_again=None
    ):
        """
        Args:
            parent: Parent window
            chain: Completed ScriptChain
            total_xp: Dictionary mapping skill name to XP gained
            on_run_again: Optional callback to run the chain again
        """
        super().__init__(parent)

        self.on_run_again = on_run_again
        self.chain = chain

        # Window configuration
        self.title("Chain Complete")
        self.geometry("500x600")
        self.transient(parent)
        self.grab_set()

        # Make dialog modal
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Configure layout
        self.rowconfigure(0, weight=0)  # Title
        self.rowconfigure(1, weight=0)  # Stats frame
        self.rowconfigure(2, weight=1)  # XP frame (scrollable)
        self.rowconfigure(3, weight=0)  # Buttons
        self.columnconfigure(0, weight=1)

        # ============ Title ============
        title_frame = customtkinter.CTkFrame(self, fg_color="#2E7D32", corner_radius=0)
        title_frame.grid(row=0, column=0, sticky="ew")

        lbl_title = customtkinter.CTkLabel(
            title_frame,
            text="✅ Chain Complete!",
            font=("Roboto Bold", 20),
            text_color="#FFFFFF",
        )
        lbl_title.pack(pady=20)

        # ============ Chain Info ============
        info_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(20, 10))

        lbl_chain_name = customtkinter.CTkLabel(
            info_frame,
            text=f"Chain: {chain.name}",
            font=("Roboto Medium", 16),
            text_color="#DCE4EE",
            anchor="w",
        )
        lbl_chain_name.pack(anchor="w", pady=(0, 10))

        # Calculate statistics
        total_time = chain.total_time_minutes()
        completed = sum(
            1 for e in chain.entries if e.status == ChainEntryStatus.COMPLETED
        )
        skipped = sum(1 for e in chain.entries if e.status == ChainEntryStatus.SKIPPED)
        failed = sum(1 for e in chain.entries if e.status == ChainEntryStatus.FAILED)
        total_scripts = len(chain.entries)

        # Stats grid
        stats_grid = customtkinter.CTkFrame(
            info_frame, fg_color="#1A1A1A", corner_radius=8
        )
        stats_grid.pack(fill="x", pady=(0, 10))
        stats_grid.columnconfigure(0, weight=1)
        stats_grid.columnconfigure(1, weight=1)

        # Total time
        self._create_stat_row(
            stats_grid, 0, "Total Time:", self._format_time(total_time)
        )

        # Scripts completed
        self._create_stat_row(
            stats_grid, 1, "Scripts Completed:", f"{completed}/{total_scripts}"
        )

        # Scripts skipped (if any)
        if skipped > 0:
            self._create_stat_row(
                stats_grid, 2, "Scripts Skipped:", f"{skipped}", "#FFA726"
            )

        # Scripts failed (if any)
        if failed > 0:
            self._create_stat_row(
                stats_grid, 3, "Scripts Failed:", f"{failed}", "#EF5350"
            )

        # ============ XP Summary ============
        xp_label = customtkinter.CTkLabel(
            self,
            text="Experience Gained:",
            font=("Roboto Medium", 14),
            text_color="#DCE4EE",
            anchor="w",
        )
        xp_label.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 5))

        # Scrollable XP list
        xp_frame = customtkinter.CTkScrollableFrame(
            self,
            fg_color="#0F0F0F",
            corner_radius=8,
        )
        xp_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        xp_frame.columnconfigure(0, weight=1)
        xp_frame.columnconfigure(1, weight=0)

        # Display XP by skill
        if total_xp and any(xp > 0 for xp in total_xp.values()):
            row_idx = 0
            for skill, xp in sorted(total_xp.items()):
                if xp > 0:
                    skill_label = customtkinter.CTkLabel(
                        xp_frame,
                        text=skill.capitalize(),
                        font=("Roboto", 13),
                        text_color="#DCE4EE",
                        anchor="w",
                    )
                    skill_label.grid(row=row_idx, column=0, sticky="w", padx=10, pady=5)

                    xp_label = customtkinter.CTkLabel(
                        xp_frame,
                        text=f"+{xp:,} XP",
                        font=("Roboto Medium", 13),
                        text_color="#66BB6A",
                        anchor="e",
                    )
                    xp_label.grid(row=row_idx, column=1, sticky="e", padx=10, pady=5)
                    row_idx += 1

            # Total XP
            total_xp_amount = sum(total_xp.values())
            separator = customtkinter.CTkFrame(xp_frame, height=2, fg_color="#2E2E2E")
            separator.grid(
                row=row_idx, column=0, columnspan=2, sticky="ew", padx=10, pady=5
            )

            total_label = customtkinter.CTkLabel(
                xp_frame,
                text="Total XP",
                font=("Roboto Bold", 14),
                text_color="#DCE4EE",
                anchor="w",
            )
            total_label.grid(row=row_idx + 1, column=0, sticky="w", padx=10, pady=5)

            total_xp_label = customtkinter.CTkLabel(
                xp_frame,
                text=f"+{total_xp_amount:,} XP",
                font=("Roboto Bold", 14),
                text_color="#66BB6A",
                anchor="e",
            )
            total_xp_label.grid(row=row_idx + 1, column=1, sticky="e", padx=10, pady=5)
        else:
            # No XP tracked
            no_xp_label = customtkinter.CTkLabel(
                xp_frame,
                text="XP tracking not available",
                font=("Roboto", 12),
                text_color="#707070",
            )
            no_xp_label.pack(pady=20)

        # ============ Buttons ============
        button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        # Run Again button (only if callback provided)
        if on_run_again:
            btn_run_again = customtkinter.CTkButton(
                button_frame,
                text="🔄 Run Again",
                font=("Roboto Medium", 13),
                fg_color="#1976D2",
                hover_color="#2196F3",
                command=self._on_run_again,
                height=36,
            )
            btn_run_again.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        # Close button
        btn_close = customtkinter.CTkButton(
            button_frame,
            text="Close",
            font=("Roboto Medium", 13),
            fg_color="#424242",
            hover_color="#616161",
            command=self._on_close,
            height=36,
        )
        close_column = 1 if on_run_again else 0
        close_columnspan = 1 if on_run_again else 2
        btn_close.grid(
            row=0, column=close_column, columnspan=close_columnspan, sticky="ew"
        )

    # ============ Private Methods ============

    def _create_stat_row(
        self, parent, row: int, label: str, value: str, value_color: str = "#DCE4EE"
    ):
        """
        Create a stat row with label and value.

        Args:
            parent: Parent frame
            row: Row index
            label: Stat label
            value: Stat value
            value_color: Color for value text
        """
        lbl = customtkinter.CTkLabel(
            parent,
            text=label,
            font=("Roboto", 13),
            text_color="#A0A0A0",
            anchor="w",
        )
        lbl.grid(row=row, column=0, sticky="w", padx=15, pady=8)

        val = customtkinter.CTkLabel(
            parent,
            text=value,
            font=("Roboto Medium", 13),
            text_color=value_color,
            anchor="e",
        )
        val.grid(row=row, column=1, sticky="e", padx=15, pady=8)

    def _format_time(self, minutes: int) -> str:
        """
        Format minutes as "Xh Ym" or "Ym".

        Args:
            minutes: Time in minutes

        Returns:
            Formatted string
        """
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}h {mins}m"
        else:
            return f"{mins}m"

    def _on_run_again(self):
        """Handle Run Again button click."""
        self.destroy()
        if self.on_run_again:
            self.on_run_again()

    def _on_close(self):
        """Handle Close button click."""
        self.destroy()
