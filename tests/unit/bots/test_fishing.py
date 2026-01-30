import os

from model.osrs.fishing import OSRSFishing


def test_defaults():
    bot = OSRSFishing()

    assert bot.fish_type == "Raw shrimp"
    assert bot.inventory_mode == "Drop"


def test_save_options_updates_fields():
    bot = OSRSFishing()

    options = {
        "running_time": 42,
        "take_breaks": [" "],
        "fish_type": "Raw shrimp",
        "inventory_mode": "Drop",
    }

    bot.save_options(options)

    assert bot.running_time == 42
    assert bot.take_breaks is True
    assert bot.fish_type == "Raw shrimp"
    assert bot.inventory_mode == "Drop"
    assert bot.options_set is True


def test_get_fish_template_path():
    bot = OSRSFishing()

    bot.fish_type = "Unknown"
    assert bot._get_fish_template_path() is None

    bot.fish_type = "Raw shrimp"
    shrimp_path = bot._get_fish_template_path()
    assert shrimp_path is not None
    assert shrimp_path.endswith(os.path.join("fishing_spots", "raw_shrimp.png"))
