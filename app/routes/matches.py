from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
)

from app import db, limiter
from app.models.match import Match
from app.models.claim import ClaimRequest


matches = Blueprint("matches", __name__)


# --------------------------------------------------
# POTENTIAL MATCHES
# --------------------------------------------------

@matches.route("/matches")
def potential_matches():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    # Get matches belonging to this user's lost reports.
    user_matches = (
        Match.query
        .join(Match.lost_item)
        .filter(Match.lost_item.has(user_id=user_id))
        .order_by(Match.score.desc())
        .all()
    )

    # --------------------------------------------------
    # GET CLAIM STATUS FOR EACH MATCH
    # --------------------------------------------------

    claim_statuses = {}

    if user_matches:

        match_ids = [
            match.id
            for match in user_matches
        ]

        claims = (
            ClaimRequest.query
            .filter(
                ClaimRequest.claimant_user_id == user_id,
                ClaimRequest.match_id.in_(match_ids)
            )
            .all()
        )

        for claim in claims:
            claim_statuses[claim.match_id] = claim.status

    return render_template(
        "matches.html",
        matches=user_matches,
        claim_statuses=claim_statuses
    )


# --------------------------------------------------
# REQUEST VERIFICATION
# --------------------------------------------------

@matches.route(
    "/matches/<int:match_id>/claim",
    methods=["POST"]
)
@limiter.limit("10 per hour")
def request_claim(match_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    match = Match.query.get_or_404(match_id)

    # --------------------------------------------------
    # SECURITY CHECK
    # Only the owner of the lost item can request
    # verification for this match.
    # --------------------------------------------------

    if match.lost_item.user_id != user_id:

        flash(
            "You are not authorized to request verification for this match.",
            "error"
        )

        return redirect(
            url_for("matches.potential_matches")
        )

    # --------------------------------------------------
    # SECURITY CHECK
    # The claimant must not also be the finder.
    # --------------------------------------------------

    if match.found_item.user_id == user_id:

        flash(
            "You cannot request verification for your own found item.",
            "error"
        )

        return redirect(
            url_for("matches.potential_matches")
        )

    # --------------------------------------------------
    # SECURITY CHECK
    # Only potential matches can be claimed.
    # --------------------------------------------------

    if match.status != "potential":

        flash(
            "This match is no longer available for verification.",
            "error"
        )

        return redirect(
            url_for("matches.potential_matches")
        )

    # --------------------------------------------------
    # PREVENT DUPLICATE REQUESTS
    # --------------------------------------------------

    existing_claim = ClaimRequest.query.filter_by(
        match_id=match.id,
        claimant_user_id=user_id
    ).first()

    if existing_claim:

        flash(
            "You have already submitted a verification request for this match.",
            "error"
        )

        return redirect(
            url_for("matches.potential_matches")
        )

    # --------------------------------------------------
    # FINDER = OWNER OF FOUND ITEM
    # --------------------------------------------------

    finder_user_id = match.found_item.user_id

    claim = ClaimRequest(
        match_id=match.id,
        claimant_user_id=user_id,
        finder_user_id=finder_user_id,
        status="pending"
    )

    db.session.add(claim)
    db.session.commit()

    flash(
        "Verification request sent to the finder.",
        "success"
    )

    return redirect(
        url_for("matches.potential_matches")
    )


# --------------------------------------------------
# INCOMING VERIFICATION REQUESTS
# --------------------------------------------------

@matches.route("/requests")
def incoming_requests():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    requests = (
        ClaimRequest.query
        .filter_by(
            finder_user_id=user_id
        )
        .order_by(
            ClaimRequest.created_at.desc()
        )
        .all()
    )

    return render_template(
        "incoming_requests.html",
        requests=requests
    )


# --------------------------------------------------
# APPROVE REQUEST
# --------------------------------------------------

@matches.route(
    "/requests/<int:claim_id>/approve",
    methods=["POST"]
)
def approve_request(claim_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    claim = ClaimRequest.query.get_or_404(claim_id)

    # --------------------------------------------------
    # SECURITY CHECK
    # Only the finder can approve this request.
    # --------------------------------------------------

    if claim.finder_user_id != user_id:

        flash(
            "You are not authorized to approve this request.",
            "error"
        )

        return redirect(
            url_for("matches.incoming_requests")
        )

    # --------------------------------------------------
    # PREVENT RE-PROCESSING
    # --------------------------------------------------

    if claim.status != "pending":

        flash(
            "This verification request has already been processed.",
            "error"
        )

        return redirect(
            url_for("matches.incoming_requests")
        )

    # Approve the claim.
    claim.status = "approved"

    db.session.commit()

    flash(
        "Verification request approved. Private item access can now be granted.",
        "success"
    )

    return redirect(
        url_for("matches.incoming_requests")
    )


# --------------------------------------------------
# REJECT REQUEST
# --------------------------------------------------

@matches.route(
    "/requests/<int:claim_id>/reject",
    methods=["POST"]
)
def reject_request(claim_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    claim = ClaimRequest.query.get_or_404(claim_id)

    # --------------------------------------------------
    # SECURITY CHECK
    # Only the finder can reject this request.
    # --------------------------------------------------

    if claim.finder_user_id != user_id:

        flash(
            "You are not authorized to reject this request.",
            "error"
        )

        return redirect(
            url_for("matches.incoming_requests")
        )

    # --------------------------------------------------
    # PREVENT RE-PROCESSING
    # --------------------------------------------------

    if claim.status != "pending":

        flash(
            "This verification request has already been processed.",
            "error"
        )

        return redirect(
            url_for("matches.incoming_requests")
        )

    # Reject the claim.
    claim.status = "rejected"

    db.session.commit()

    flash(
        "Verification request rejected.",
        "success"
    )

    return redirect(
        url_for("matches.incoming_requests")
    )