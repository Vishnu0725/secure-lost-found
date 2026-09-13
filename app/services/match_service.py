from app import db

from app.models.found_item import FoundItem
from app.models.lost_item import LostItem
from app.models.match import Match
from app.services.matching import calculate_match_score


MATCH_THRESHOLD = 50.0


def find_matches_for_lost_item(lost_item):
    """
    Compare one lost item against existing found items.

    Only potential matches above the threshold are stored.
    """

    found_items = FoundItem.query.all()

    matches_created = []

    for found_item in found_items:

        score = calculate_match_score(
            lost_item,
            found_item
        )

        if score < MATCH_THRESHOLD:
            continue

        existing_match = Match.query.filter_by(
            lost_item_id=lost_item.id,
            found_item_id=found_item.id
        ).first()

        if existing_match:
            existing_match.score = score
            continue

        match = Match(
            lost_item_id=lost_item.id,
            found_item_id=found_item.id,
            score=score,
            status="potential"
        )

        db.session.add(match)
        matches_created.append(match)

    db.session.commit()

    return matches_created


def find_matches_for_found_item(found_item):
    """
    Compare one found item against existing lost items.

    This ensures matching works regardless of which report
    was submitted first.
    """

    lost_items = LostItem.query.all()

    matches_created = []

    for lost_item in lost_items:

        score = calculate_match_score(
            lost_item,
            found_item
        )

        if score < MATCH_THRESHOLD:
            continue

        existing_match = Match.query.filter_by(
            lost_item_id=lost_item.id,
            found_item_id=found_item.id
        ).first()

        if existing_match:
            existing_match.score = score
            continue

        match = Match(
            lost_item_id=lost_item.id,
            found_item_id=found_item.id,
            score=score,
            status="potential"
        )

        db.session.add(match)
        matches_created.append(match)

    db.session.commit()

    return matches_created