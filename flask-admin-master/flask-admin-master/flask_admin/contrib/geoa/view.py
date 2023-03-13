from flask_admin.contrib.sqla import ModelView as SQLAModelView
from flask_admin.contrib.geoa import form, typefmt


class ModelView(SQLAModelView):
    model_form_converter = form.AdminModelConverter
    column_type_formatters = typefmt.DEFAULT_FORMATTERS
    tile_layer_url = None
    tile_layer_attribution = None
