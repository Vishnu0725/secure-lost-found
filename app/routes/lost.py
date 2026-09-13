from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from app import db
from app.models.lost_item import LostItem
from app.services.match_service import find_matches_for_lost_item


lost = Blueprint("lost", __name__)


@lost.route("/report/lost", methods=["GET", "POST"])
def report_lost():

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        item_name = request.form.get("item_name", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        location_lost = request.form.get("location_lost", "").strip()
        date_lost = request.form.get("date_lost", "").strip()

        # Check required fields
        if not all([
            item_name,
            category,
            description,
            location_lost,
            date_lost
        ]):
            flash(
                "Please fill in all required fields.",
                "error"
            )
            return redirect(
                url_for("lost.report_lost")
            )

        # Server-side length validation
        if len(item_name) > 100:
            flash(
                "Item name must be 100 characters or less.",
                "error"
            )
            return redirect(
                url_for("lost.report_lost")
            )

        if len(category) > 50:
            flash(
                "Category must be 50 characters or less.",
                "error"
            )
            return redirect(
                url_for("lost.report_lost")
            )

        if len(description) > 2000:
            flash(
                "Description must be 2000 characters or less.",
                "error"
            )
            return redirect(
                url_for("lost.report_lost")
            )

        if len(location_lost) > 200:
            flash(
                "Location must be 200 characters or less.",
                "error"
            )
            return redirect(
                url_for("lost.report_lost")
            )

        # Convert date from form to Python date
        try:
            lost_date = datetime.strptime(
                date_lost,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            flash(
                "Please enter a valid date.",
                "error"
            )
            return redirect(
                url_for("lost.report_lost")
            )

        # Create lost item
        item = LostItem(
            user_id=session["user_id"],
            item_name=item_name,
            category=category,
            description=description,
            location_lost=location_lost,
            date_lost=lost_date
        )

        db.session.add(item)
        db.session.commit()

        find_matches_for_lost_item(item)

        flash(
            "Lost item reported successfully.",
            "success"
        )

        return redirect(
            url_for("lost.report_lost")
        )

    return render_template("report_lost.html")