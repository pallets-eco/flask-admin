PyMongo backend
===============

Pretty simple PyMongo backend.

Flask-Admin does not make assumptions about document structure, so you
will have to configure ModelView to do what you need it to do.

This is bare minimum you have to provide for Flask-Admin view to work
with PyMongo:

 1. Provide list of columns by setting `column_list` property
 2. Provide form to use by setting `form` property
 3. When instantiating :class:`flask.ext.admin.contrib.pymongo.ModelView` class, you have to provide PyMongo collection object

This is minimal PyMongo view::

  class UserForm(wtf.Form):
      name = wtf.TextForm('Name')
      email = wtf.TextForm('Email')

  class UserView(ModelView):
      column_list = ('name', 'email')
      form = UserForm

  if __name__ == '__main__':
      admin = Admin(app)

      # 'db' is PyMongo database object
      admin.add_view(UserView(db['users']))

On top of that you can add sortable columns, filters, text search, etc.

For more documentation, check :doc:`api/mod_contrib_pymongo` documentation.

PyMongo integration example is `here <https://github.com/mrjoes/flask-admin/tree/master/examples/pymongo>`_.
