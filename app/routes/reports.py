from flask import Blueprint, render_template, redirect, url_for, session

from app.models.lost_item import LostItem
from app.models.found_item import FoundItem


reports = Blueprint("reports", __name__)


@reports.route("/my-reports")
def my_reports():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    lost_reports = LostItem.query.filter_by(
        user_id=user_id
    ).order_by(
        LostItem.created_at.desc()
    ).all()

    found_reports = FoundItem.query.filter_by(
        user_id=user_id
    ).order_by(
        FoundItem.created_at.desc()
    ).all()

    return render_template(
        "my_reports.html",
        lost_reports=lost_reports,
        found_reports=found_reports
    )