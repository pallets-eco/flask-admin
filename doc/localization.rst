Localization
============

Flask-Admin makes it possible for you to serve your application in more than one language. To do this, it makes use of
the `Flask-BabelEx <http://github.com/mrjoes/flask-babelex/>`_ package for handling translations. This package is a
fork of the popular `Flask-Babel <http://github.com/mitshuhiko/flask-babel/>`_ package, with the following features:

1. It is API-compatible with Flask-Babel
2. It allows distribution of translations with Flask extensions
3. It aims to be more configurable than Flask-Babel

Currently *Flask-BabelEx* is the only supported way of enabling localization support in Flask-Admin.

How to enable localization
--------------------------

1. Install Flask-BabelEx::

    pip install flask-babelex

2. Initialize Flask-BabelEx by creating instance of `Babel` class::

	from flask import app
	from flask.ext.babelex import Babel

	app = Flask(__name__)
	babel = Babel(app)

3. Create a locale selector function::

	@babel.localeselector
	def get_locale():
		# Put your logic here. Application can store locale in
		# user profile, cookie, session, etc.
		return 'en'

4. Initialize Flask-Admin as usual.

You can check the `babel` example to see localization in action. When running this example, you can change the
locale simply by adding a query parameter, like *?en=<locale name>* to the URL. For example, a French version of
the application should be accessible at:
`http://localhost:5000/admin/userview/?lang=fr <http://localhost:5000/admin/userview/?lang=fr>`_.
