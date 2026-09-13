from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from app import db, limiter
from app.models.user import User
from app.models.lost_item import LostItem
from app.models.found_item import FoundItem
from app.models.match import Match
from app.models.claim import ClaimRequest
from app.models.message import Message


auth = Blueprint("auth", __name__)


# -------------------------
# REGISTER
# -------------------------

@auth.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Check empty fields
        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("auth.register"))

        # Server-side length validation
        if len(name) > 100:
            flash(
                "Name must be 100 characters or less.",
                "error"
            )
            return redirect(url_for("auth.register"))

        if len(email) > 255:
            flash(
                "Email address is too long.",
                "error"
            )
            return redirect(url_for("auth.register"))

        # Check password length
        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "error"
            )
            return redirect(url_for("auth.register"))

        if len(password) > 128:
            flash(
                "Password must be 128 characters or less.",
                "error"
            )
            return redirect(url_for("auth.register"))

        # Check existing account
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash(
                "An account with this email already exists.",
                "error"
            )
            return redirect(url_for("auth.register"))

        # Create user
        user = User(
            name=name,
            email=email
        )

        # Securely hash password
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash(
            "Account created successfully. Please sign in.",
            "success"
        )

        return redirect(url_for("auth.login"))

    return render_template("register.html")


# -------------------------
# LOGIN
# -------------------------

@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Find user
        user = User.query.filter_by(email=email).first()

        # Verify credentials
        if user and user.check_password(password):

            # Remove any previous session data
            session.clear()

            # Store authenticated user
            session["user_id"] = user.id
            session["user_name"] = user.name

            return redirect(url_for("auth.dashboard"))

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template("login.html")


# -------------------------
# DASHBOARD
# -------------------------

@auth.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    lost_reports_count = LostItem.query.filter_by(
        user_id=user_id
    ).count()

    found_reports_count = FoundItem.query.filter_by(
        user_id=user_id
    ).count()

    pending_requests_count = ClaimRequest.query.filter_by(
        finder_user_id=user_id,
        status="pending"
    ).count()

    potential_matches_count = (
        Match.query
        .join(Match.lost_item)
        .filter(
            Match.lost_item.has(
                user_id=user_id
            )
        )
        .count()
    )

    # Count unread messages received by the current user.
    unread_messages_count = Message.query.filter_by(
        recipient_user_id=user_id,
        is_read=False
    ).count()

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name", "User"),
        lost_reports_count=lost_reports_count,
        found_reports_count=found_reports_count,
        potential_matches_count=potential_matches_count,
        pending_requests_count=pending_requests_count,
        unread_messages_count=unread_messages_count
    )


# -------------------------
# APPROVED MESSAGES
# -------------------------

@auth.route("/messages")
def messages():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    # Only show approved verification requests where the
    # logged-in user is either the claimant or the finder.
    approved_conversations = (
        ClaimRequest.query
        .filter(
            ClaimRequest.status == "approved",
            (
                (ClaimRequest.claimant_user_id == user_id)
                |
                (ClaimRequest.finder_user_id == user_id)
            )
        )
        .order_by(
            ClaimRequest.updated_at.desc()
        )
        .all()
    )

    return render_template(
        "messages_list.html",
        conversations=approved_conversations,
        current_user_id=user_id
    )


# -------------------------
# LOGOUT
# -------------------------

@auth.route("/logout", methods=["POST"])
def logout():

    session.clear()

    flash(
        "You have been signed out.",
        "success"
    )

    return redirect(url_for("home"))