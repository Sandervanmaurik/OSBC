import os

from model.osrs.mining import OSRSMining


def test_defaults():
    bot = OSRSMining()

    assert bot.ore_type == "Any"
    assert bot.inventory_mode == "Drop"
    assert bot.ore_tag_color_name == "Pink"
    assert bot.bank_tag_color_name == "Green"


def test_save_options_updates_fields():
    bot = OSRSMining()

    options = {
        "running_time": 42,
        "take_breaks": [" "],
        "ore_type": "Copper",
        "ore_tag_color_name": "Pink",
        "inventory_mode": "Drop",
        "bank_tag_color_name": "Green",
    }

    bot.save_options(options)

    assert bot.running_time == 42
    assert bot.take_breaks is True
    assert bot.ore_type == "Copper"
    assert bot.ore_tag_color_name == "Pink"
    assert bot.inventory_mode == "Drop"
    assert bot.bank_tag_color_name == "Green"
    assert bot.options_set is True


def test_get_ore_template_path():
    bot = OSRSMining()

    bot.ore_type = "Any"
    assert bot._get_ore_template_path() is None

    bot.ore_type = "Copper"
    copper_path = bot._get_ore_template_path()
    assert copper_path is not None
    assert copper_path.endswith(os.path.join("mining", "copper_ore.png"))

    bot.ore_type = "Tin"
    tin_path = bot._get_ore_template_path()
    assert tin_path is not None
    assert tin_path.endswith(os.path.join("mining", "tin_ore.png"))

    bot.ore_type = "Iron"
    iron_path = bot._get_ore_template_path()
    assert iron_path is not None
    assert iron_path.endswith(os.path.join("mining", "iron_ore.png"))
