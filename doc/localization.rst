Localization
============

Flask-Admin uses the `Flask-BabelEx <http://github.com/mrjoes/flask-babelex/>`_ package to handle translations.

Flask-BabelEx is a fork of Flask-Babel with following features:

1. It is API-compatible with Flask-Babel
2. It allows distribution of translations with Flask extensions
3. Much more configurable

If Flask-Admin can not import Flask-BabelEx, it disables localization support completely.

How to enable localization
--------------------------

1. Initialize Flask-BabelEx by creating instance of `Babel` class::

	from flask import app
	from flask.ext.babelex import Babel

	app = Flask(__name__)
	babel = Babel(app)

2. Create locale selector function::

	@babel.localeselector
	def get_locale():
		# Put your logic here. Application can store locale in
		# user profile, cookie, session, etc.
		return 'en'

3. Initialize Flask-Admin as usual.

You can check `babel` example to see localization in action. To change locale, add *?en=<locale name>* to the URL. For example, URL
can look like: `http://localhost:5000/admin/userview/?lang=fr <http://localhost:5000/admin/userview/?lang=fr>`_.
