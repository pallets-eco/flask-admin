import json

from nose.tools import eq_, ok_, raises, assert_true
from speaklater import make_lazy_string

from . import setup
from .test_basic import CustomModelView, create_models

class Translator:
    translate = False

    def __call__(self, string):
        if self.translate:
            return 'Translated: "{0}"'.format(string)
        else:
            return string

def test_column_label_translation():
    app, db, admin = setup()

    Model1, _ = create_models(db)

    translated = Translator()
    label = make_lazy_string(translated, 'Column1')

    view = CustomModelView(Model1, db.session,
                           column_list=['test1', 'test3'],
                           column_labels=dict(test1=label),
                           column_filters=('test1',))

    translated.translate = True
    non_lazy_groups = view._get_filter_groups()
    json.dumps(non_lazy_groups)  # Filter dict is JSON serializable.
    ok_(translated('Column1') in non_lazy_groups)  # Label was translated.
