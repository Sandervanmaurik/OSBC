import pathlib
from typing import Any

import customtkinter as ctk

fonts_path = pathlib.Path(__file__).parent
ctk.FontManager.load_font(str(fonts_path.joinpath("CascadiaCode.ttf")))

# Type alias for CTkFont (customtkinter lacks stubs)
CTkFont = Any


def get_font(
    family: str = "Trebuchet MS",
    size: int = 14,
    weight: str = "normal",
    slant: str = "roman",
    underline: bool = False,
) -> CTkFont:
    """
    Gets a font object with the given parameters. This is a wrapper for ctk.CTkFont. Provides
    defaults for app theme fonts.
    """
    return ctk.CTkFont(
        family=family, size=size, weight=weight, slant=slant, underline=underline
    )


def title_font() -> CTkFont:
    """
    Preset for titles (largest).
    """
    return get_font(size=24, weight="bold")


def heading_font(size: int = 18) -> CTkFont:
    """
    Preset for headings.
    """
    return get_font(size=size, weight="bold")


def subheading_font(size: int = 16) -> CTkFont:
    """
    Preset for subheadings.
    """
    return get_font(size=size, weight="bold")


def body_large_font(size: int = 15) -> CTkFont:
    """
    Preset for body text.
    """
    return get_font(size=size)


def body_med_font(size: int = 14) -> CTkFont:
    """
    Preset for body text.
    """
    return get_font(size=size)


def button_med_font(size: int = 14) -> CTkFont:
    """
    Preset for button text.
    """
    return get_font(size=size, weight="bold")


def button_small_font(size: int = 12) -> CTkFont:
    """
    Preset for button text.
    """
    return get_font(size=size, weight="bold")


def small_font(size: int = 12) -> CTkFont:
    """
    Preset for small text, such as captions or footnotes.
    """
    return get_font(size=size)


def micro_font(size: int = 10) -> CTkFont:
    """
    Preset for micro text, such as version stamps.
    """
    return get_font(size=size)


def log_font(size: int = 12) -> CTkFont:
    """
    Preset for log text.
    """
    return get_font(family="Cascadia Code", size=size)
