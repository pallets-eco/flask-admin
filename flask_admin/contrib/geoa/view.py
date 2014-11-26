from flask.ext.admin.contrib.sqla import ModelView as SQLAModelView
from flask.ext.admin.contrib.geoa import form, typefmt


class ModelView(SQLAModelView):
    model_form_converter = form.AdminModelConverter
    column_type_formatters = typefmt.DEFAULT_FORMATTERS
