from datetime import date

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def text_similarity(text_a, text_b):
    """
    Calculate TF-IDF cosine similarity between two pieces of text.

    Returns a value between 0 and 1.
    """

    text_a = (text_a or "").strip().lower()
    text_b = (text_b or "").strip().lower()

    if not text_a or not text_b:
        return 0.0

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    try:
        matrix = vectorizer.fit_transform([
            text_a,
            text_b
        ])
    except ValueError:
        return 0.0

    similarity = cosine_similarity(
        matrix[0:1],
        matrix[1:2]
    )[0][0]

    return float(similarity)


def category_similarity(category_a, category_b):
    """
    Exact category match.
    """

    if not category_a or not category_b:
        return 0.0

    return 1.0 if (
        category_a.strip().lower()
        == category_b.strip().lower()
    ) else 0.0


def location_similarity(location_a, location_b):
    """
    Uses TF-IDF similarity for locations.
    """

    return text_similarity(
        location_a,
        location_b
    )


def date_similarity(date_a, date_b):
    """
    Gives higher similarity to dates that are close together.

    Same day       -> 1.0
    1 day apart    -> 0.9
    2 days apart   -> 0.8
    ...
    10+ days apart -> 0.0
    """

    if not isinstance(date_a, date):
        return 0.0

    if not isinstance(date_b, date):
        return 0.0

    difference = abs(
        (date_a - date_b).days
    )

    if difference >= 10:
        return 0.0

    return max(
        0.0,
        1.0 - (difference * 0.1)
    )


def calculate_match_score(lost_item, found_item):
    """
    Calculate an overall potential-match score.

    This is NOT an ownership decision.
    It only measures similarity between two reports.
    """

    lost_text = (
        f"{lost_item.item_name} "
        f"{lost_item.description}"
    )

    found_text = (
        f"{found_item.item_name} "
        f"{found_item.description}"
    )

    text_score = text_similarity(
        lost_text,
        found_text
    )

    category_score = category_similarity(
        lost_item.category,
        found_item.category
    )

    location_score = location_similarity(
        lost_item.location_lost,
        found_item.location_found
    )

    date_score = date_similarity(
        lost_item.date_lost,
        found_item.date_found
    )

    # Weighted score.
    #
    # Text        = 70%
    # Category    = 15%
    # Location    = 10%
    # Date        = 5%

    final_score = (
        text_score * 0.70
        + category_score * 0.15
        + location_score * 0.10
        + date_score * 0.05
    )

    return round(
        final_score * 100,
        2
    )