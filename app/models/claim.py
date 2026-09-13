from datetime import datetime

from app import db


class ClaimRequest(db.Model):
    __tablename__ = "claim_requests"

    __table_args__ = (
        db.UniqueConstraint(
            "match_id",
            "claimant_user_id",
            name="uq_claim_match_claimant"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    match_id = db.Column(
        db.Integer,
        db.ForeignKey("matches.id"),
        nullable=False
    )

    claimant_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    finder_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # --------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------

    match = db.relationship(
        "Match",
        backref="claim_requests"
    )

    claimant = db.relationship(
        "User",
        foreign_keys=[claimant_user_id],
        backref="submitted_claim_requests"
    )

    finder = db.relationship(
        "User",
        foreign_keys=[finder_user_id],
        backref="received_claim_requests"
    )

    # Messages belonging to this verification request.
    # Messages will only be usable after the claim is approved.
    messages = db.relationship(
        "Message",
        backref="claim",
        cascade="all, delete-orphan",
        lazy=True
    )