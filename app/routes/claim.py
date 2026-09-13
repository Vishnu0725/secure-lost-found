from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request
)

from app import db, limiter
from app.models.claim import ClaimRequest
from app.models.message import Message


claim = Blueprint("claim", __name__)


# --------------------------------------------------
# SECURE MESSAGING
# --------------------------------------------------

@claim.route(
    "/requests/<int:request_id>/messages",
    methods=["GET", "POST"]
)
@limiter.limit("30 per hour", methods=["POST"])
def messages(request_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    claim_request = ClaimRequest.query.get_or_404(request_id)

    # Messaging is allowed only after verification approval.
    if claim_request.status != "approved":
        flash(
            "Messaging is available only after verification is approved.",
            "error"
        )
        return redirect(url_for("matches.potential_matches"))

    # Only the claimant or finder belonging to this exact
    # verification request can access the conversation.
    if user_id not in (
        claim_request.claimant_user_id,
        claim_request.finder_user_id
    ):
        flash(
            "You are not authorized to access this conversation.",
            "error"
        )
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":

        body = request.form.get("body", "").strip()

        # Prevent empty messages.
        if not body:
            flash(
                "Message cannot be empty.",
                "error"
            )
            return redirect(
                url_for(
                    "claim.messages",
                    request_id=request_id
                )
            )

        # Keep messages reasonably sized.
        if len(body) > 2000:
            flash(
                "Message is too long. Please keep it under 2000 characters.",
                "error"
            )
            return redirect(
                url_for(
                    "claim.messages",
                    request_id=request_id
                )
            )

        # Determine the other participant.
        if user_id == claim_request.claimant_user_id:
            recipient_user_id = claim_request.finder_user_id
        else:
            recipient_user_id = claim_request.claimant_user_id

        message = Message(
            claim_id=claim_request.id,
            sender_user_id=user_id,
            recipient_user_id=recipient_user_id,
            body=body
        )

        db.session.add(message)
        db.session.commit()

        return redirect(
            url_for(
                "claim.messages",
                request_id=request_id
            )
        )

    # Retrieve messages belonging only to this claim.
    conversation = (
        Message.query
        .filter_by(
            claim_id=claim_request.id
        )
        .order_by(
            Message.created_at.asc()
        )
        .all()
    )

    # Mark messages sent to the current user as read.
    unread_messages = (
        Message.query
        .filter_by(
            claim_id=claim_request.id,
            recipient_user_id=user_id,
            is_read=False
        )
        .all()
    )

    for message in unread_messages:
        message.is_read = True

    if unread_messages:
        db.session.commit()

    return render_template(
        "messages.html",
        claim_request=claim_request,
        messages=conversation,
        current_user_id=user_id
    )