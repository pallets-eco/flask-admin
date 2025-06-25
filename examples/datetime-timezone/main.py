from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask
from flask import jsonify
from flask import request
from flask import session
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.model import typefmt
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


# model
class Base(DeclarativeBase):
    pass


# app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
# Create dummy secret key so we can use sessions
app.config["SECRET_KEY"] = "123456789"
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Article(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(30))
    last_edit: Mapped[datetime] = mapped_column(DateTime(timezone=True))


# admin
def date_format(view, value):
    """
    Ensure consistent date format and inject class for timezone.js parser.
    """
    if value is None:
        return ""
    return Markup(
        f'<span class="timezone-aware">{value.strftime("%Y-%m-%d %H:%M:%S")}</span>'
    )


MY_DEFAULT_FORMATTERS = dict(typefmt.BASE_FORMATTERS)
MY_DEFAULT_FORMATTERS.update(
    {
        datetime: date_format,
    }
)


class TimezoneAwareModelView(ModelView):
    column_type_formatters = MY_DEFAULT_FORMATTERS
    extra_js = ["/static/js/timezone.js"]

    def on_model_change(self, form, model, is_created):
        """
        Save datetime fields after converting from session['timezone'] to UTC.
        """
        user_timezone = session["timezone"]

        for field_name, field_value in form.data.items():
            if isinstance(field_value, datetime):
                # Convert naive datetime to timezone-aware datetime
                aware_time = field_value.replace(tzinfo=ZoneInfo(user_timezone))

                # Convert the time to UTC
                utc_time = aware_time.astimezone(ZoneInfo("UTC"))

                # Assign the UTC time to the model
                setattr(model, field_name, utc_time)

        super().on_model_change(form, model, is_created)


# inherit TimeZoneAwareModelView to make any admin page timezone-aware
class TimezoneAwareBlogModelView(TimezoneAwareModelView):
    column_labels = {
        "last_edit": "Last Edit (local time)",
    }


# compare with regular ModelView to display data as saved on db
class BlogModelView(ModelView):
    column_labels = {
        "last_edit": "Last Edit (UTC)",
    }


# Flask views
@app.route("/")
def index():
    return '<a href="/admin/timezone_aware_article">Click me to get to Admin!</a>'


@app.route("/set_timezone", methods=["POST"])
def set_timezone():
    """
    Save timezone to session so that datetime inputs can be correctly converted to UTC.
    """
    session.permanent = True
    timezone = request.get_json()
    if timezone:
        session["timezone"] = timezone
        return jsonify({"message": "Timezone set successfully"}), 200
    else:
        return jsonify({"error": "Invalid timezone"}), 400


# create db on the fly
with app.app_context():
    Base.metadata.drop_all(db.engine)
    Base.metadata.create_all(db.engine)
    db.session.add(
        Article(text="Written at 9:00 UTC", last_edit=datetime(2024, 8, 8, 9, 0, 0))
    )
    db.session.commit()
    admin = Admin(app, name="microblog")
    admin.add_view(
        BlogModelView(Article, db.session, name="Article", endpoint="article")
    )
    admin.add_view(
        TimezoneAwareBlogModelView(
            Article,
            db.session,
            name="Timezone Aware Article",
            endpoint="timezone_aware_article",
        )
    )

if __name__ == "__main__":
    app.run(debug=True)
