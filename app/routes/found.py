import os
import secrets
from datetime import datetime
from pathlib import Path

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
    abort
)

from PIL import Image, UnidentifiedImageError

from app import db
from app.models.found_item import FoundItem
from app.models.claim import ClaimRequest
from app.services.match_service import find_matches_for_found_item


found = Blueprint("found", __name__)


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def allowed_file(filename):
    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in ALLOWED_EXTENSIONS


def get_private_upload_folder():
    project_root = Path(__file__).resolve().parents[2]

    upload_folder = project_root / "private_uploads"
    upload_folder.mkdir(exist_ok=True)

    return upload_folder


# --------------------------------------------------
# REPORT FOUND ITEM
# --------------------------------------------------

@found.route("/report/found", methods=["GET", "POST"])
def report_found():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        item_name = request.form.get("item_name", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        location_found = request.form.get("location_found", "").strip()
        date_found = request.form.get("date_found", "").strip()

        image = request.files.get("image")

        if not all([
            item_name,
            category,
            description,
            location_found,
            date_found
        ]):
            flash(
                "Please fill in all required fields.",
                "error"
            )
            return redirect(
                url_for("found.report_found")
            )

        # Server-side length validation
        if len(item_name) > 100:
            flash(
                "Item name must be 100 characters or less.",
                "error"
            )
            return redirect(
                url_for("found.report_found")
            )

        if len(category) > 50:
            flash(
                "Category must be 50 characters or less.",
                "error"
            )
            return redirect(
                url_for("found.report_found")
            )

        if len(description) > 2000:
            flash(
                "Description must be 2000 characters or less.",
                "error"
            )
            return redirect(
                url_for("found.report_found")
            )

        if len(location_found) > 200:
            flash(
                "Location must be 200 characters or less.",
                "error"
            )
            return redirect(
                url_for("found.report_found")
            )

        if not image or not image.filename:
            flash(
                "Please upload an image of the found item.",
                "error"
            )
            return redirect(
                url_for("found.report_found")
            )

        if not allowed_file(image.filename):
            flash(
                "Invalid image type. Use JPG, JPEG, PNG or WEBP.",
                "error"
            )
            return redirect(
                url_for("found.report_found")
            )

        try:
            found_date = datetime.strptime(
                date_found,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            flash(
                "Please enter a valid date.",
                "error"
            )
            return redirect(
                url_for("found.report_found")
            )

        # --------------------------------------------------
        # FILE SIZE CHECK
        # --------------------------------------------------

        image.seek(0, os.SEEK_END)
        file_size = image.tell()
        image.seek(0)

        if file_size > MAX_FILE_SIZE:
            flash(
                "Image is too large. Maximum size is 5 MB.",
                "error"
            )
            return redirect(
                url_for("found.report_found")
            )

        # --------------------------------------------------
        # VERIFY REAL IMAGE
        # --------------------------------------------------

        try:
            with Image.open(image) as img:
                image_format = img.format
                img.verify()

        except (UnidentifiedImageError, OSError):
            flash(
                "The uploaded file is not a valid image.",
                "error"
            )
            return redirect(
                url_for("found.report_found")
            )

        if image_format not in {
            "JPEG",
            "PNG",
            "WEBP"
        }:
            flash(
                "Unsupported image format.",
                "error"
            )
            return redirect(
                url_for("found.report_found")
            )

        # Re-open after verify()
        image.seek(0)

        try:

            with Image.open(image) as img:

                img.load()

                private_folder = get_private_upload_folder()

                # Never trust original filename.
                random_name = secrets.token_hex(32)

                extension_map = {
                    "JPEG": ".jpg",
                    "PNG": ".png",
                    "WEBP": ".webp"
                }

                safe_extension = extension_map[img.format]

                filename = random_name + safe_extension

                image_path = private_folder / filename

                # Re-encode image.
                save_format = img.format

                if save_format == "JPEG":

                    if img.mode not in ("RGB", "L"):
                        img = img.convert("RGB")

                    img.save(
                        image_path,
                        format="JPEG",
                        quality=90,
                        optimize=True
                    )

                elif save_format == "PNG":

                    img.save(
                        image_path,
                        format="PNG",
                        optimize=True
                    )

                elif save_format == "WEBP":

                    img.save(
                        image_path,
                        format="WEBP",
                        quality=90
                    )

        except (UnidentifiedImageError, OSError):

            flash(
                "The image could not be processed securely.",
                "error"
            )

            return redirect(
                url_for("found.report_found")
            )

        # --------------------------------------------------
        # SAVE FOUND ITEM
        # --------------------------------------------------

        item = FoundItem(
            user_id=session["user_id"],
            item_name=item_name,
            category=category,
            description=description,
            location_found=location_found,
            date_found=found_date,
            image_path=filename
        )

        try:

            db.session.add(item)
            db.session.commit()

        except Exception:

            db.session.rollback()

            if image_path.exists():
                image_path.unlink()

            flash(
                "The report could not be saved. Please try again.",
                "error"
            )

            return redirect(
                url_for("found.report_found")
            )

        # --------------------------------------------------
        # FIND MATCHES
        # --------------------------------------------------

        find_matches_for_found_item(item)

        flash(
            "Found item reported successfully. "
            "Your image is stored privately.",
            "success"
        )

        return redirect(
            url_for("found.report_found")
        )

    return render_template("report_found.html")


# --------------------------------------------------
# PRIVATE IMAGE
# --------------------------------------------------

@found.route("/private-image/<filename>")
def private_image(filename):

    # --------------------------------------------------
    # 1. USER MUST BE LOGGED IN
    # --------------------------------------------------

    if "user_id" not in session:
        abort(401)

    current_user_id = session["user_id"]

    # --------------------------------------------------
    # 2. FIND THE FOUND ITEM
    # --------------------------------------------------

    item = FoundItem.query.filter_by(
        image_path=filename
    ).first()

    if not item:
        abort(404)

    # --------------------------------------------------
    # 3. AUTHORIZATION
    # --------------------------------------------------

    # The finder who uploaded the item can always
    # access their own private image.
    is_finder = (
        item.user_id == current_user_id
    )

    # Check whether this user is the claimant
    # of an APPROVED verification request for
    # this exact match.
    approved_claim = (
        ClaimRequest.query
        .filter_by(
            claimant_user_id=current_user_id,
            status="approved"
        )
        .join(ClaimRequest.match)
        .filter(
            ClaimRequest.match.has(
                found_item_id=item.id
            )
        )
        .first()
    )

    is_approved_claimant = (
        approved_claim is not None
    )

    # --------------------------------------------------
    # 4. DENY EVERYONE ELSE
    # --------------------------------------------------

    if not is_finder and not is_approved_claimant:
        abort(403)

    # --------------------------------------------------
    # 5. RESOLVE PRIVATE FILE PATH
    # --------------------------------------------------

    private_folder = (
        get_private_upload_folder()
        .resolve()
    )

    image_path = (
        private_folder / filename
    ).resolve()

    # --------------------------------------------------
    # 6. PREVENT PATH TRAVERSAL
    # --------------------------------------------------

    if private_folder not in image_path.parents:
        abort(403)

    # --------------------------------------------------
    # 7. FILE MUST EXIST
    # --------------------------------------------------

    if not image_path.is_file():
        abort(404)

    # --------------------------------------------------
    # 8. SEND WITHOUT BROWSER CACHING
    # --------------------------------------------------

    response = send_file(
        image_path,
        conditional=False
    )

    response.headers["Cache-Control"] = (
        "no-store, private"
    )

    response.headers["Pragma"] = "no-cache"

    response.headers["X-Content-Type-Options"] = (
        "nosniff"
    )

    return response