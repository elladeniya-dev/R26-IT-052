"""Titles that name only a bottom garment must never be used as outerwear or tops,
even when the crawler filed them under blazer/top."""

from app.s_outfit_generator import normalize_category, title_names_only_a_bottom


def test_pants_filed_as_blazer_are_bottoms():
    for title in (
        "Flared Leg Formal Pant- Pastel Pink",
        "Pink Flared Leg Formal Pant",
        "Vineyard Green Flared Formal Pant",
    ):
        assert normalize_category("top", "blazer", title) == "bottom"


def test_real_outerwear_and_tops_are_untouched():
    assert normalize_category("top", "blazer", "Printed Black And White Trendy Blazer") == "outerwear"
    assert normalize_category("outerwear", "jacket", "Denim Jean Jacket") == "outerwear"
    assert normalize_category("top", "top", "Lace Crop Top - 280826") == "top"


def test_short_sleeve_is_not_shorts():
    assert not title_names_only_a_bottom("Short Sleeve Blazer - 080626")
    assert normalize_category("top", "top", "Short Sleeve Blazer - 080626") == "outerwear"
    assert normalize_category("top", "top", "Short Sleeve Tee") == "top"


def test_titles_naming_another_garment_too_are_left_as_labelled():
    assert not title_names_only_a_bottom("Linen Pant Set")
    assert normalize_category("dress", "set", "Linen Pant Set") == "dress"
    assert not title_names_only_a_bottom("Jumpsuit Pantsuit Set")
    assert not title_names_only_a_bottom("Denim Jean Jacket")


def test_whole_words_only():
    assert not title_names_only_a_bottom("Pantone Colour Tee")
    assert title_names_only_a_bottom("Luxe Flared Pant")
    assert title_names_only_a_bottom("Seamless 6inch Biker Short")


def test_bottoms_stay_bottoms():
    assert normalize_category("bottom", "pants", "Luxe Flared Pant") == "bottom"
    assert normalize_category("skirt", "skirt", "Aeris Skort") == "bottom"
