import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


db = SQLAlchemy()
csrf = CSRFProtect()

# --------------------------------------------------
# RATE LIMITING
# --------------------------------------------------

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv(
        "RATELIMIT_STORAGE_URI",
        "memory://"
    )
)


def create_app():
    app = Flask(__name__)

    # --------------------------------------------------
    # SECURITY
    # --------------------------------------------------

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "securefind-development-secret-key"
    )

    # Maximum incoming HTTP request size.
    # Slightly above the 5 MB image limit to allow multipart overhead.
    app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024

    # Session cookie security
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Enable secure cookies only when explicitly enabled.
    # Keep this False for local HTTP development.
    app.config["SESSION_COOKIE_SECURE"] = (
        os.getenv("SECURE_COOKIES", "0") == "1"
    )

    csrf.init_app(app)

    # --------------------------------------------------
    # RATE LIMITER
    # --------------------------------------------------

    limiter.init_app(app)

    # --------------------------------------------------
    # SECURITY HEADERS
    # --------------------------------------------------

    @app.after_request
    def add_security_headers(response):

        response.headers["X-Content-Type-Options"] = "nosniff"

        response.headers["X-Frame-Options"] = "DENY"

        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        return response

    # --------------------------------------------------
    # DATABASE
    # --------------------------------------------------

    # Use Neon PostgreSQL when DATABASE_URL is available
    # (for example, on Vercel).
    #
    # Fall back to local SQLite when DATABASE_URL is not set.
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///securefind.db"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # --------------------------------------------------
    # REGISTER ROUTES
    # --------------------------------------------------

    from app.routes.auth import auth
    app.register_blueprint(auth)

    from app.routes.lost import lost
    app.register_blueprint(lost)

    from app.routes.found import found
    app.register_blueprint(found)

    from app.routes.reports import reports
    app.register_blueprint(reports)

    from app.routes.matches import matches
    app.register_blueprint(matches)

    from app.routes.claim import claim
    app.register_blueprint(claim)

    # --------------------------------------------------
    # IMPORT MODELS
    # --------------------------------------------------

    from app.models.user import User
    from app.models.lost_item import LostItem
    from app.models.found_item import FoundItem
    from app.models.match import Match
    from app.models.claim import ClaimRequest
    from app.models.message import Message

    # --------------------------------------------------
    # CREATE DATABASE TABLES
    # --------------------------------------------------

    with app.app_context():
        db.create_all()

    # --------------------------------------------------
    # HOME PAGE
    # --------------------------------------------------

    @app.route("/")
    def home():
        return render_template("home.html")

    return app