from datetime import datetime

from app import db


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # The verification request this message belongs to.
    claim_id = db.Column(
        db.Integer,
        db.ForeignKey("claim_requests.id"),
        nullable=False
    )

    # User who sent the message.
    sender_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # User who receives the message.
    recipient_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Message content.
    body = db.Column(
        db.Text,
        nullable=False
    )

    # Whether the recipient has opened/read the message.
    is_read = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # --------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------

    sender = db.relationship(
        "User",
        foreign_keys=[sender_user_id]
    )

    recipient = db.relationship(
        "User",
        foreign_keys=[recipient_user_id]
    )