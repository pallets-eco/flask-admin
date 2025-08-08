from flask_admin.contrib.geoa import form
from flask_admin.contrib.geoa import typefmt
from flask_admin.contrib.sqla import ModelView as SQLAModelView


class ModelView(SQLAModelView):
    model_form_converter = form.AdminModelConverter
    column_type_formatters = typefmt.DEFAULT_FORMATTERS
    # tile_layer_url is prefixed with '//' in flask_admin/static/admin/js/form.js
    # Leave it as None or set it to a string starting with a hostname, NOT "http".
    tile_layer_url = None
    tile_layer_attribution = None
