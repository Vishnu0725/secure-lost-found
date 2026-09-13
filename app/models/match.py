from datetime import datetime

from app import db


class Match(db.Model):
    __tablename__ = "matches"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    lost_item_id = db.Column(
        db.Integer,
        db.ForeignKey("lost_items.id"),
        nullable=False
    )

    found_item_id = db.Column(
        db.Integer,
        db.ForeignKey("found_items.id"),
        nullable=False
    )

    score = db.Column(
        db.Float,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="potential"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    lost_item = db.relationship(
        "LostItem",
        backref=db.backref(
            "matches",
            lazy=True
        )
    )

    found_item = db.relationship(
        "FoundItem",
        backref=db.backref(
            "matches",
            lazy=True
        )
    )