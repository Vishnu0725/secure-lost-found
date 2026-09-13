from datetime import date
from types import SimpleNamespace

from app.services.matching import calculate_match_score


def create_item(
    name,
    category,
    description,
    lost_or_found_location,
    item_date
):
    return SimpleNamespace(
        item_name=name,
        category=category,
        description=description,
        location_lost=lost_or_found_location,
        location_found=lost_or_found_location,
        date_lost=item_date,
        date_found=item_date
    )


def test_similar_items_get_high_score():

    lost_item = create_item(
        "Black Leather Wallet",
        "Wallet",
        "Black leather wallet with a scratch near the bottom right corner.",
        "College Library",
        date(2026, 10, 8)
    )

    found_item = create_item(
        "Black Leather Wallet",
        "Wallet",
        "Black leather wallet with a small scratch on the bottom right corner.",
        "College Library",
        date(2026, 10, 8)
    )

    score = calculate_match_score(
        lost_item,
        found_item
    )

    print(f"\nSimilar item score: {score}%")

    assert score > 50


def test_different_items_get_lower_score():

    lost_item = create_item(
        "Black Leather Wallet",
        "Wallet",
        "Black leather wallet with a scratch near the bottom right corner.",
        "College Library",
        date(2026, 10, 8)
    )

    found_item = create_item(
        "Blue Backpack",
        "Bag",
        "Large blue backpack with two outside pockets.",
        "Railway Station",
        date(2026, 10, 20)
    )

    score = calculate_match_score(
        lost_item,
        found_item
    )

    print(f"\nDifferent item score: {score}%")

    assert score < 50