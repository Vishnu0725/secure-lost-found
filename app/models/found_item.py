from datetime import datetime
from app import db


class FoundItem(db.Model):
    __tablename__ = "found_items"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    item_name = db.Column(
        db.String(100),
        nullable=False
    )

    category = db.Column(
        db.String(50),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    location_found = db.Column(
        db.String(200),
        nullable=False
    )

    date_found = db.Column(
        db.Date,
        nullable=False
    )

    image_path = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )